#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from starlette.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from .app import App
from .db import cache
from .settings import PORT
from starlette.requests import Request

app = App(debug=True)
app.mount('/static', StaticFiles(directory="static"), name='static')

import qllr.blueprints as bp
app.mount('/elo', bp.balance_api)
app.mount('/stats', bp.submission)
app.mount('/scoreboard', bp.scoreboard)
app.mount('/player', bp.player)
app.mount('/ratings', bp.ratings)
app.mount('/matches', bp.matches)
app.mount('/steam_api', bp.steam_api)
app.mount('/export_rating', bp.export_rating)
app.mount('/deprecated', bp.deprecated)


@app.route('/')
def http_root(request: Request):
    return RedirectResponse(request.url_for('MatchesHtml'))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
