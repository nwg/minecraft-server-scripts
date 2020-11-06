# Scripts and systemd service files for a minecraft server

Note: update.py originally from https://github.com/eclair4151/MinecraftUpdater
The script originally used screen, this version uses systemd and a fifo

* `mkdir -p $HOME/minecraft`
* `cd $HOME/minecraft`
* `git clone git@github.com:nwg/minecraft-server-scripts.git`
* `cp minecraft-server-scripts/minecraft.{service,socket} ~/.config/systemd/user`
* `systemctl --user enable minecraft.service`
* `crontab -e`

```sh
0 * * * * /home/griswold/minecraft/minecraft-server-scripts/update.py
```

* Get world files from somewhere if you have one; place into $HOME/minecraft/world/
* edit eula.txt, set eula=true
* (Optional) Create whitelist.json

```json
[
  {
    "uuid": "some-uuid-string",
    "name": "some-user-name"
  }
]
```

* `python3 minecraft-server-scripts/update.py`
