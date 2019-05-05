import pickle
import numpy as np

from music21 import instrument, note, stream, chord, duration

import os
import sys
import tensorflow as tf

# Jako argumenty uruchamianego programu podajemy kolejno:
# - ścieżkę do pliku z nutami, który zapisaliśmy przy uczeniu sieci,
# - ścieżkę do pliku zawierającego wytrenowany model,
# - nazwę (ścieżkę) wyjściowego pliku MIDI, do którego chcemy zapisać wygenerowany utwór.
plik_z_nutami = sys.argv[1]
ścieżka_do_modelu = sys.argv[2]
plik_wyjściowy = sys.argv[3]

# ładujemy plik z zapisanymi wcześniej nutami
with open(plik_z_nutami, 'rb') as ścieżka:
    nuty = list(pickle.load(ścieżka))

nazwy_dźwięków = sorted(set(nuty))
liczba_dźwięków = len(nazwy_dźwięków)

# mapowanie nut na wartości liczbowe - tak jak przy trenowaniu sieci
nuty_int = dict((n, i) for i, n in enumerate(nazwy_dźwięków))

długość_sekwencji = 100  # musi być taka sama, jak przy trenowaniu modelu
wejście_sieci = []
# tu robimy mniej więcej to samo, co przed trenowaniem sieci, z tym że nie potrzebujemy już "wyjścia"
for i in range(0, len(nuty) - długość_sekwencji):
    sekwencja_wejściowa = nuty[i:i + długość_sekwencji]
    sekwencja_wyjściowa = nuty[i + długość_sekwencji]
    wejście_sieci.append([nuty_int[n] for n in sekwencja_wejściowa])

liczba_wzorców = len(wejście_sieci)

znormalizowane_wejście = np.reshape(wejście_sieci, (liczba_wzorców, długość_sekwencji, 1))
znormalizowane_wejście = znormalizowane_wejście / float(liczba_dźwięków)

model = tf.keras.models.load_model(ścieżka_do_modelu, compile=False)  # ładujemy wytrenowany model
opt = tf.train.RMSPropOptimizer(
    0.002)  # optymalizator - tu nam nie będzie tak naprawdę potrzebny, ale musimy go dodać, żeby model się poprawnie skompilował

model.compile(loss='categorical_crossentropy', optimizer=opt)

# dekoder dźwięków z liczb na tekstową reprezentację
int_nuty = dict((i, n) for i, n in enumerate(nazwy_dźwięków))

# Żeby zacząć, potrzebujemy jakiejkolwiek bazy, pierwszego wzorca - losujemy go z tej bazy, którą już mamy, tzn. z tych nut, które zapisaliśmy.
# Jeśli sieć nie jest przetrenowana, jeśli nie jest zbyt rozbudowana w stosunku do liczby utworów, nie ma większego ryzyka, że wygenerujemy utwór bardzo podobny do któregoś z utworów z bazy uczącej. Można także wylosować dźwięki należące do początkowego wzorca, ale istnieje ryzyko, że będzie to zupełny chaos i tak też potem może wyglądać cały wygenerowany utwór. Możemy także jako pierwszy wzorzec wziąć utwór spoza bazy uczącej, mając jednak na uwadze, by utwór ten nie zawierał dźwięków nieznanych dotąd naszej sieci.
# Jednak w prostej wersji wystarczy nam wylosowanie fragmentu z nut, które już mamy. Dla pewności możemy też w oddzielnym pliku MIDI zapisać fragment, który służy za pierwszy wzorzec i porównać ten wzorzec z wygenerowanym utworem.
start = np.random.randint(0, len(wejście_sieci) - 1)
wzorzec = wejście_sieci[start]  # losowa sekwencja z danych wejściowych

wyjście = []

# tutaj za pomocą wytrenowanego modelu wygenerujemy kolejne dźwięki - czy też - póki co - ich tekstową reprezentację
for note_index in range(500):
    wzorzec_wejściowy = np.reshape(wzorzec, (1, len(wzorzec), 1))  # to przekażemy na wejście sieci
    wzorzec_wejściowy = wzorzec_wejściowy / float(liczba_dźwięków)  # + normalizacja

    wektor_wyjściowy = model.predict(wzorzec_wejściowy, verbose=0)  # wektor z wartościami zwróconymi przez sieć dla poszczególnych nut i akordów - wyjście sieci

    # sprawdzamy, która nuta została wybrana przez sieć (która ma najwyższy wynik na wyjściu)
    nuta_int = np.argmax(wektor_wyjściowy)
    # wynikiem, który dodajemy do właściwego wyjścia, jest nuta (lub akord) w reprezentacji tekstowej
    wynik = int_nuty[nuta_int]
    wyjście.append(wynik)

    # dodajemy liczbową reprezentację wygenerowanej nuty do wzorca, którego używamy jako bazy przewidywań
    wzorzec.append(nuta_int)
    # przesuwamy wzorzec o jedno miejsce w prawo - odrzucamy pierwszy dźwięk, dodajemy ten przed chwilą dodany
    wzorzec = wzorzec[1:len(wzorzec)]

# W tym skrypcie rytm generowany jest półlosowo - dlaczego "pół", o tym poniżej.
# Rytm (choć to, co będziemy generować, do końca rytmem nie jest, to duże uproszczenie) składa się z dwóch elementów:
# - momentu rozpoczęcia trwania nuty na skali czasu (offset) - tutaj losować będziemy postęp offsetu, tzn. o ile później od rozpoczęcia poprzedniego dźwięku/akordu ma się rozpocząć kolejny,
# długości trwania dźwięku - czyli przez jaki czas od rozpoczęcia swego trwania dźwięk będzie grany.
# Musimy rozróżnić offset od długości trwania dźwięku z jednego prostego powodu - w muzyce rzadko kiedy jest tak, że dźwięk zawsze kończy się z momentem rozpoczęcia kolejnego - często jest nawet tak, że kilka dźwięków jest granych na tle ciągle trwającego w tle akordu.
# Żeby jednak nasz rytm miał muzyczny sens, musimy zwrócić uwagę na przynajmniej kilka spraw:
# - długość trwania dźwięku ani zależności czasowe pomiędzy kolejnymi dźwiękami nie mogą być losowane z ciągłego przedziału od zera do nieskończoności - prowadziłoby to do przedziwnych efektów, jak na przykład kilkuminutowa przerwa między kolejnymi dźwiękami, gdzie pierwszy trwa 14 milisekund, a kolejny 3 minuty - dlatego też definiujemy zbiór dopuszczalnych, dyskretnych wartości;
# - zazwyczaj pewne wartości rytmiczne występują częściej niż inne - np. możemy się spodziewać, że ćwierćnuta będzie w utworze występować częściej niż cała nuta z kropką - dlatego też musimy jeszcze trochę zmniejszyć losowość spowodować, by rzeczywiście pewne wartości występowały częściej niż inne - stąd w naszych zbiorach dopuszczalne wartości nie będą występwały z jednakowym prawdopodobieństwem, niektóre będziemy faworyzować poprzez powtórzenie ich na liście;
# - w większości przypadków struktura rytmiczna utworu opiera się na tym, że pewne sekwencje rytmiczne się powtarzają - ale nie każda i nie zawsze - więc powinniśmy po raz kolejny zmniejszyć poziom losowości, tym razem poprzez losowanie powtórzeń sekwencji.

postęp_offsetów = [0.5, 0.5, 0.5, 1.0, 1.5]  # dopuszczalne wartości postępu offsetu
# dopuszczalne wartości rytmiczne (jednostką bazową jest ćwierćnuta) -
# przy czym do każdej z nich należy dodać jeszcze różnicę offsetu,
# a więc jest to w istocie zbiór dopuszczalnych "przedłużeń" dźwięku -
# 0 NIE oznacza, że dźwięk zostanie pominięty
wartości_rytmiczne = [0.0, 0.0, 0.5, 1.0, 1.5, 2.0]

offsety = []  # lista kolejnych wartości postępu offsetu
rytm = []  # lista kolejnych wartości rytmicznych w utworze (długości trwania dźwięków)

while len(offsety) < 501:  # generujemy 501 wartości postępu offsetu i wartości rytmicznych
    długość_sekwencji = np.random.randint(2, 6)  # losujemy, ile dźwięków/akordów wystąpi w naszej sekwencji
    liczba_powtórzeń = np.random.randint(1, 5)  # i ile razy sekwencja zostanie powtórzona
    sekwencja_offsetów = []  # kolejne postępy offsetu w sekwencji
    sekwencja_rytmiczna = []  # kolejne długości trwania dźwięków w sekwencji - nazwa `sekwencja_rytmiczna` może być nieco myląca (bo w istocie offset też się do rytmu zalicza, i to bardzo), ale lepszej nie wymyśliłem

    for j in range(0, długość_sekwencji):
        # do sekwencji offsetów dodajemy wylosowaną z listy `postęp_offsetów` wartość
        sekwencja_offsetów.append(postęp_offsetów[np.random.randint(0, len(postęp_offsetów))])
        # do sekwencji długości trwania dźwięków dodajemy ostatnią (przed chwilą dodaną) wartość postępu offsetu (a więc co najmniej ósemkę) + wylosowaną dodatkową długość trwania dźwięku
        sekwencja_rytmiczna.append(
            sekwencja_offsetów[-1] + wartości_rytmiczne[np.random.randint(0, len(wartości_rytmiczne))])

    # obydwie sekwencje powtarzamy tyle razy, ile wylosowaliśmy
    for j in range(0, liczba_powtórzeń):
        offsety += sekwencja_offsetów
        rytm += sekwencja_rytmiczna

# tu zaczyna się generowanie pliku MIDI na podstawie tego, co zwróciła nam sieć
offset = 0  # offset będziemy zwiększać o kolejne wylosowane wartości - startujemy od zera, bo zakładamy, że nie ma pauzy na początku (przynajmniej w prostej wersji)
licznik = 0  # licznik będzie służył do pobierania wylosowanych wartości rytmicznych i postępu offsetu
partytura = []  # tu będziemy przechowywać wygenerowane dźwięki
for wzorzec in wyjście:
    d = duration.Duration()  # tworzymy obiekt klasy Duration, dzięki któremu będziemy mogli ustalić długość trwania dźwięku/akordu
    d.quarterLength = rytm[licznik]  # pobieramy koleją wylosowaną długość trwania dźwięku/akordu (gdzie jednostką czasu jest liczba ćwierćnut)

    # jeśli wzorzec jest akordem (zawiera kropkę lub jest liczbą, zgodnie z tym co zaimplementowaliśmy przy trenowaniu sieci), musimy stworzyć akord
    if ('.' in wzorzec) or wzorzec.isdigit():
        dźwięki_składowe = list(map(int, wzorzec.split('.')))
        nuty_w_akordzie = []
        for n in dźwięki_składowe:
            nuta = note.Note(n)  # tworzymy obiekt nuty
            nuta.storedInstrument = instrument.Piano()  # wybieramy fortepian jako instrument
            nuty_w_akordzie.append(nuta)

        akord = chord.Chord(nuty_w_akordzie)  # z nut składowych tworzymy akord

        akord.offset = offset  # ustalamy moment rozpoczęcia trwania akordu
        nuta.duration = d  # ustalamy długość trwania akordu
        partytura.append(akord)  # dodajemy akord do partytury
    # jeśli jest pojedynczą nutą
    else:
        nuta = note.Note(wzorzec)  # tworzymy obiekt nuty
        nuta.offset = offset  # ustalamy moment rozpoczęcia trwania nuty
        nuta.duration = d  # ustalamy długość trwania dźwięku
        nuta.storedInstrument = instrument.Piano()  # wybieramy fortepian jako instrument
        partytura.append(nuta)  # dodajemy utworzony dźwięk do partytury

    offset += offsety[licznik]  # zwiększamy offset - tak by kolejna nuta nie nakładała się na obecną
    licznik += 1

# z utworzonej partytury musimi utworzyć obiekt klasy Strea, by móc zapisać ją jako plik MIDI
midi_stream = stream.Stream(partytura)

# zapisujemy wygenerowaną partyturę do pliku MIDI
midi_stream.write('midi', fp=plik_wyjściowy)
