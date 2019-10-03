# Dokumentaatio
Alustava dokumentaatio (kesken)

## Lyhyesti

Sovellus on testattavissa Herokussa, ja sen pitäisi toimia ainakin chromiumilla ja firefoxilla.

[Heroku](https://demo-tsoha.herokuapp.com/)

### Huom!
Heroku poistaa palvelimelle tallennetut tiedostot palvelimen uudelleenkäynnistyksen yhteydessä, joka aiheuttaa virheitä.
Ongelma on ratkaistavissa esim. jollain pilvipalvelulla, mutta sovelluksen perustoiminnallisuuden demonstroinnin kannalta ei kuvien pitempiaikaista säilyvyyttä Herokussa tarvita. 

## Käyttöohje

Sovelluksen käytön aloittaminen vaatii rekisteröitymistä ja kirjautumista. Sovelluksen muun käytön ei pitäisi vaatia erillisiä ohjeita.
Tarkempaa opastusta löytyy sovelluksesta sisäänkirjautumisen jälkeen.

## Asennusohje

### Development
Sovellus vaatii toimiakseen development-ympäristössä vähintään version 3.7.4 Pythonin, 3.29.0 SQLiten ja requirements.txt sisältämät Python-kirjastot ja niiden mahdolliset riippuvuudet.
Tarvittavat kirjastot voi asentaa esimerkiksi pip-package installerilla `pip install -r requirements.txt`-komennolla.

Sovelluksen saa käyntiin suorittamalla run_dev.sh tiedoston.

### Heroku
Sovelluksen voi deployata Herokuun muuten sellaisenaan, mutta vaaditaan `HEROKU=1` ja `DATABASE_URL` ympäristömuuttujat, joista jälkimmäisen arvo kertoo PostgreSQL-tietokannan Connection URI-osoitteen libpq vaatimassa formaatissa, halutessaan voi suoraan käyttää Herokun Postgres-lisäosaa.

## Käyttötapaukset ja toiminnot

Tarkoituksena on laatia sivusto, johon käyttäjä pystyy rekisteröitymään ja lataamaan tiedostoja, pääasiassa kuvia. Tiedostoille pystyy merkitsemään tageja, tagien avulla voi hakea tiedostoja. Käyttäjän tiedostot näkyvät vain hänelle itselleen. Pääkäyttäjä voi säätää käyttäjille quotan levytilan käyttöön, jota käyttäjä ei pysty ylittämään.

Toimintoja:
- Kirjautuminen, rekisteröinti
- Tiedostojen lataus sivustolle
- Tiedoston tagien muuttaminen
- Tiedostojen haku tageilla
- Tiedostojen poisto
- Quota käyttäjille

## Tietokantarakenne

SQL-lauseet tietokantataulujen luomiseen

```SQL
CREATE TABLE User (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	admin BOOLEAN NOT NULL,
	username VARCHAR(32) NOT NULL UNIQUE,
	max_quota INTEGER NOT NULL,
	used_quota INTEGER NOT NULL,
	password_hash BLOB NOT NULL,
	password_salt BLOB NOT NULL
);
```

```SQL
CREATE TABLE Session_token (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	session_token VARCHAR(128) NOT NULL UNIQUE,
	user_id INTEGER,
	FOREIGN KEY(user_id) REFERENCES User(id)
);
```

```SQL
CREATE TABLE File (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	filename VARCHAR(255) NOT NULL UNIQUE,
	user_id INTEGER,
	FOREIGN KEY(user_id) REFERENCES User(id)
);
```

```SQL
CREATE TABLE Tag (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name VARCHAR(128) NOT NULL,
	used_count INTEGER NOT NULL,
	user_id INTEGER NOT NULL,
	FOREIGN KEY(user_id) REFERENCES User(id)
);
```

```SQL
CREATE TABLE association_file_tag (
	tag_id INTEGER,
	file_id INTEGER,
	PRIMARY KEY (tag_id, file_id),
	FOREIGN KEY(tag_id) REFERENCES Tag(id),
	FOREIGN KEY(file_id) REFERENCES File(id)
);
```

[Tietokantakaavio](https://github.com/ArktinenKarpalo/demo-tsoha/blob/master/docs/tietokantakaavio.png)

## Jatkokehitysideat