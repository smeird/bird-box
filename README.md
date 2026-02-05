# bird-box

Bird Box is a lightweight, single-page web dashboard for a birdhouse camera. It renders live device status from MQTT topics (battery, LED, motion delta) and displays camera snapshots by reading the `/snapshots/` directory listing, showing each JPG with a timestamp caption and a modal preview. The page is styled with Tailwind via CDN and runs entirely in the browser with no build step.

## Snapshots directory

Place camera images in `snapshots/` at the repository root so they are served at `/snapshots/`. The gallery expects JPG filenames in the format `YYYYMMDD_HHMMSS.jpg` so it can format timestamps in the UI. The directory is tracked in Git with a `.gitkeep` placeholder so it exists when you deploy.
