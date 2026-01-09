*Four legendary heroes were fighting for the land of Vindinium*

*Making their way in the dangerous woods*

*Slashing goblins and stealing gold mines*

*And looking for a tavern where to drink their gold*

---

## 🐍 Python Rewrite (2026)

This repository is being rewritten in **Python 3.11+ with FastAPI**. The new implementation maintains full compatibility with the original game mechanics while leveraging modern async capabilities.

- **Python Implementation**: See `python/` directory
- **Documentation**: See `specs/001-vindinium-python-rewrite/`
- **Contributing**: See `CONTRIBUTING.md` (especially for Copilot agents)
- **Quick Start**: See `python/QUICKSTART.md`

---

### Warning

The vindinium dot org website has been discontinued, and the domain now belongs to Internet parasites.

### Installation

Feel free to install a local instance for your private tournaments.
You need [sbt](http://www.scala-sbt.org/), a MongoDB instance running, and a Unix machine (only Linux has been tested, tho).

```sh
git clone git://github.com/ornicar/vindinium
cd vindinium
cd client
./build.sh
cd ..
sbt compile
sbt run
```

Vindinium is now running on `http://localhost:9000`.

#### Optional reverse proxy

Here's an exemple of nginx configuration:

```
server {
 listen 80;
 server_name my-domain.org;

  location / {
    proxy_http_version 1.1;
    proxy_read_timeout 24h;
    proxy_set_header Host $host;
    proxy_pass  http://127.0.0.1:9000/;
  }
}
```

### Developing on the Client Side stack

while the Server runs with a `sbt run`, you can go in another terminal in the `client/` folder and:

- Install once the dependencies with `npm install` (This requires nodejs to be installed)
- Be sure to have `grunt` installed with `npm install -g grunt-cli`
- Use `grunt` to compile client sources and watch for client source changes.

### Credits

Kudos to:

- [vjousse](https://github.com/vjousse) for the UI and testing
- [veloce](https://github.com/veloce) for the JavaScript and testing
- [gre](https://github.com/gre) for the shiny new JS playground
