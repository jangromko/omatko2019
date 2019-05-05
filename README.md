# Dysonanse nie tylko poznawcze. Muzyka generatywna (OMatKo 2019)
Niniejsze repozytorium zawiera prezentację i kod źródłowy z Ogólnopolskiej Matematycznej Konferencji Studentów „OMatKo!!!” 2019 we Wrocławiu, z referatu „Dysonanse nie tylko poznawcze. Muzyka generatywna”

# Uruchamianie skryptów

## Trenowanie sieci
Trenowanie sieci polecam uruchamiać w [Google Colab](https://colab.research.google.com/) – chyba że dysponujesz TPU na swoim prywatnym komputerze. W Google Colab nie jest konieczne instalowanie jakichkolwiek bibliotek, wszystko powinno być dostępne bez dodatowej konfiguracji.
Oryginalny kod Colab Notebook, służący do trenowania sieci, znajduje się pod adresem https://colab.research.google.com/drive/1fxjnNudlA0KgYYUEgKn0zLySolJlCBtI – jest on także dostępny w tym repozytorium.
Należy pamiętać o włączeniu akceleracji TPU na początku pracy z Colabem (dla każdego Colab Notebook oddzielnie): Edit → Notebook settings → Hardware accelerator → TPU.

## Generowanie utworów

Generowanie utworów można już robić lokalnie, powinno to trwać do 5-7 minut, w zależności od parametrów maszyny.

Do wygenerowania utworów potrzebne będą dwa pliki, zapisywane przy trenowaniu sieci – plik bazowy z nutami z bazy uczącej i plik z zapisanym modelem.
Skrypt należy uruchamiać w następujący sposób:

`python generuj.py [plik z nutami] [plik z modelem] [nazwa pliku wyjściowego MIDI]`

Do uruchomienia skryptu potrzebne będą biblioteki:
* tensorflow,
* numpy,
* music21.

Każdą z nich można zainstalować poprzez standardowe polecenie `pip install`.

# Źródła

W znacznej części kod źródłowy w tym repozytorium oparty jest o repozytorium [Classical Piano Composer](https://github.com/Skuldur/Classical-Piano-Composer).

Pełną listę źródeł można znaleźć także na przedostatnim slajdzie prezentacji.

# Uwagi końcowe

Kod źródłowy jest dość dokładnie opisany i mam nadzieję, że nie będzie problemu z jego zrozumieniem.

Wysoce wskazana jest wszelkiego rodzaju kreatywność, forkowanie repo i modyfikacje. ;-)

Pytania, uwagi i ciekawe uwtory wygenerowane na podstawie tego repozytorium można kierować na adres gromkojan[maupa]gmail.com

Dobrej zabawy!
