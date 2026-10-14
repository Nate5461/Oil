# Oil App

A practice app for trading oil futures contracts against historical settlement prices (1986–2015). It runs on your own Windows computer and opens in your web browser. No internet account or Python needed.

## Getting started (Windows)

1. **Download** the latest version: go to the [latest release](https://github.com/Nate5461/Oil/releases/latest) and click **oilApp.exe** under *Assets*.
   (Direct download link: <https://github.com/Nate5461/Oil/releases/latest/download/oilApp.exe>)
2. **Make a folder** called `Oil App` on your Desktop and move `oilApp.exe` from your Downloads folder into it.
   Don't put it in `Program Files`, because the app needs to save its data in the same folder.
3. **Double-click `oilApp.exe`.** The first time, Windows may say *"Windows protected your PC"*. Click **More info**, then **Run anyway**. You'll only have to do this once.
4. A **black window** opens, and a few seconds later the app opens in your browser at <http://127.0.0.1:8080>.

## Everyday use

| To... | Do this |
|---|---|
| Start the app | Double-click `oilApp.exe` in your `Oil App` folder |
| Quit the app | Close the black window. Closing only the browser tab leaves the app running in the background, which is harmless. |
| Get back to the app if you closed the tab | Double-click `oilApp.exe` again, or go to <http://127.0.0.1:8080> |
| Back up your progress | Copy `oil_data.sqlite` from the `Oil App` folder somewhere safe |
| Restore a backup | Close the black window, put the backed-up `oil_data.sqlite` back in the `Oil App` folder, start the app |

**Where your data lives:** the first time the app runs, it creates `oil_data.sqlite` next to `oilApp.exe`. That file holds your wallet and trades. Keep the two files together in the same folder.

**The black window:** keep it open while you use the app. Lines of text appearing in it while you click around are normal.

**The Restart button** deletes all your trades and sets your wallet to $0 (use **Deposit** to add money again). It can't be undone unless you have a backup of `oil_data.sqlite`.

## Updating to a new version

1. Close the black window.
2. Download the new `oilApp.exe` (same link as above).
3. Replace the old `oilApp.exe` in your `Oil App` folder with the new one. **Leave `oil_data.sqlite` where it is**, so your wallet and trades carry over.

## Troubleshooting

**"Windows protected your PC" when starting the app**
Click **More info**, then **Run anyway**. Windows shows this for any app that isn't signed with a paid certificate.

**The download was blocked, or `oilApp.exe` disappeared after downloading**
Some antivirus programs wrongly flag apps built the way this one is. Open **Windows Security → Virus & threat protection → Protection history**, find the oilApp.exe entry, and choose **Restore** / **Allow**. If you're not sure, ask the person who sent you this app before allowing it.

**The black window opens but the browser doesn't**
Open your browser yourself and go to <http://127.0.0.1:8080>.

**The browser says "This site can't be reached" or "Hmm, we can't reach this page"**
The app isn't running. Make sure the black window is open (start `oilApp.exe` if it isn't). If you just started it, wait a few seconds and refresh the page.

**Double-clicking `oilApp.exe` just flashes a window and opens another browser tab**
That's normal. The app is already running, so it just opens the page again instead of starting a second copy.

**The black window shows an error and says "press Enter"**
Take a screenshot of the black window and send it to the person who sent you this app. The most common cause is the app being in a folder it can't save to (like `Program Files`). Move `oilApp.exe` to the `Oil App` folder on your Desktop and try again.

**The page says "Internal Server Error"**
Look at the black window. There will be error text near the bottom. Take a screenshot of it and send it along with what you clicked just before. If the app is completely unusable and you're OK starting over:
1. Close the black window.
2. Rename `oil_data.sqlite` to `oil_data-old.sqlite` (this keeps your old data in case it can be recovered).
3. Start the app again. It creates a fresh `oil_data.sqlite` with a $50,000 wallet.

**My wallet and trades are gone (back to $50,000)**
You're probably running a different copy of `oilApp.exe`, often the one still in your Downloads folder. Each folder has its own `oil_data.sqlite`. Close the app, delete the extra copy, and always start the one in your `Oil App` folder.

**My settings on the Stats page, or the selected date, went back to the defaults**
Those are saved in your browser, not in `oil_data.sqlite`. They reset if you use a different browser or clear your browsing data. Stick to the same browser.

**A completely different website shows up at 127.0.0.1:8080**
Another program on your computer is using the same address. Close that program and start Oil App again, or let the person who sent you this app know.

**Still stuck?** Send a screenshot of the black window and a description of what you clicked to the person who sent you this app.

---

## For the developer

**Run from source** (Python 3.10+):

```
python -m pip install -r requirements.txt
python main.py
```

**Build the exe locally** on Windows: run `build.bat`. The result is `dist\oilApp.exe`.

**Publish a release:** push a tag starting with `v`.

```
git tag v1.0.1
git push origin v1.0.1
```

The `Release` GitHub Actions workflow builds `oilApp.exe` on Windows, checks that it starts from an empty folder and serves the app, then creates a GitHub release with the exe attached. The release links in this README (`releases/latest`) then point at the new version automatically.

**How the exe finds its files:** templates, static files, and a starter copy of `oil_data.sqlite` are bundled into the exe (see `oilApp.spec`). On launch, if there's no `oil_data.sqlite` next to the exe, the starter copy is copied there. After that the copy next to the exe is used and never overwritten. The starter database is whatever `oil_data.sqlite` is committed at the tagged commit, so reset it before tagging if you've been testing with it.

**Server:** waitress on `127.0.0.1:8080` (local only, so there's no firewall prompt). If the port is already in use, the exe assumes it's already running and just opens the browser.
