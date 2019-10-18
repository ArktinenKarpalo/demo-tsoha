# Dokumentaatio

## Lyhyesti

Sovellus on testattavissa Herokussa, ja sen pitäisi toimia ainakin chromiumilla ja firefoxilla.

[Heroku](https://demo-tsoha.herokuapp.com/)

### Huom!
Heroku poistaa palvelimelle tallennetut tiedostot palvelimen uudelleenkäynnistyksen yhteydessä, joka aiheuttaa virheitä.
Ongelma on ratkaistavissa esim. jollain pilvipalvelulla, mutta sovelluksen perustoiminnallisuuden demonstroinnin kannalta ei kuvien pitempiaikaista säilyvyyttä Herokussa tarvita. 

## Käyttöohje

Admin-nimisellä käyttäjällä ensimmäisen kerran rekisteröitymällä saa admin-oikeudet.

Sovelluksen käytön aloittaminen vaatii rekisteröitymistä ja kirjautumista. Sovelluksen muun käytön ei pitäisi vaatia erillisiä ohjeita.
Tarkempaa opastusta joihinkin toimintoihin löytyy kuitenkin sovelluksesta sisäänkirjautumisen jälkeen.

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
- Quotan asetus käyttäjille, ja tämän hallinta admin-käyttäjällä

## Tietokantarakenne

SQL-lauseet tietokantataulujen luomiseen SQLite-tietokannassa

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
Kysely hakuun tageilla filtteröintiin.
```SQL
SELECT id, filename
	FROM file
	WHERE file.user_id="user_id"
	AND (SELECT COUNT(*)
		FROM association_file_tag
		WHERE association_file_tag.file_id = file.id AND tag_id IN(lista include-tageista)) = include-tagien määrä
	AND NOT EXISTS (SELECT id
		FROM association_file_tag
		WHERE association_file_tag.file_id = file.id AND tag_id IN(lista exclude-tageista))
```

Kysely, jolla lasketaan hakutulosten sisältämien tagien määrä.
```SQL
SELECT tag.name, COUNT(name)
	FROM association_file_tag
	LEFT JOIN TAG ON tag_id=tag.id
	WHERE file_id IN (file_id-lista haun tuloksista)
	GROUP BY tag.name
	ORDER BY name
```

Esimerkkikyselyt sovelluksesta tiedon lisäämiselle, lukemiselle, päivittämiselle ja poistamiselle tietokannasta.

Käyttäjän rekisteröinti
```SQL
INSERT INTO USER(admin, username, max_quota, used_quota, password_hash, password_salt)
VALUES (1, 'Admin', 1000000000, 0, 'hash', 'salt')
```

Käyttäjän nimen ja quotan haku user-id:llä
```SQL
SELECT username, used_quota, max_quota
FROM USER
WHERE user.id=1
```

Käyttäjän quotan päivitys
```SQL
UPDATE User
SET used_quota=100
WHERE id=1
```

Tagin poistaminen
```SQL
DELETE FROM Tag
WHERE id=1
```

[Tietokantakaavio](https://github.com/ArktinenKarpalo/demo-tsoha/blob/master/docs/tietokantakaavio.png)

## Toteuttamatta jääneet toiminnot ja jatkokehitysideat
Kaikki suunnitellut toiminnallisuudet toteutettiin.
Sovellusta voisi kuitenkin kehittää pidemmälle ja parantaa mm. helpottamalla tagien lisäämistä tiedostoille, lisäämällä tuen useammille tiedostoformaateille.
