#!/usr/bin/python3
# -*- coding: utf-8 -*-

from config import cfg
from flask import Flask, request, jsonify, redirect, url_for, make_response
import rating
import sys
from uuid import UUID

RUN_POST_PROCESS = cfg['run_post_process']
app = Flask(__name__, static_url_path='')


@app.route('/')
def http_root():
  return app.send_static_file('index.html')


@app.route("/elo/<ids>")
@app.route("/elo_b/<ids>")
def http_elo(ids):
  try:
    return redirect(
      url_for(
        'http_elo_map',
        gametype = request.headers['X-QuakeLive-Gametype'],
        mapname  = request.headers['X-QuakeLive-Map'],
        ids = ids
      )
    )
  except KeyError:
    ids = list( map(lambda id_: int(id_), ids.split("+")) )
    return jsonify( **rating.get_for_balance_plugin(ids) )


@app.route("/elo_map/<gametype>/<mapname>/<ids>")
def http_elo_map(gametype, mapname, ids):
  ids = list( map(lambda id_: int(id_), ids.split("+")) )
  return jsonify( **rating.get_for_balance_plugin_for_certain_map(ids, gametype, mapname) )


@app.route("/steam_api/GetPlayerSummaries/")
def http_steam_api_GetPlayerSummaries():
  ids = request.args.get("steamids")
  if ids == None:
    return jsonify( ok = False, message = "Required parameter 'steamids' is missing" ), 400

  try:
    ids = ids.replace(",", " ").replace("+", " ")
    ids = list( map(lambda id_: int(id_), ids.split(" ")) )
  except ValueError as e:
    return jsonify( ok = False, message = str(e) ), 400

  players = []
  for steam_id in ids:
    player_info = rating.get_player_info( steam_id )
    if player_info["ok"]:
      if "name" in player_info["player"]:
        players.append({
          "personaname": player_info["player"]["name"],
          "steamid": str(steam_id)
        })
    else:
      return jsonify( ok = False, message = player_info["message"] ), 500

  return jsonify( ok = True, response = { "players": players } )


@app.route("/player/<int:steam_id>")
def http_player_id(steam_id):
  return jsonify( **rating.get_player_info(int(steam_id)) )


@app.route("/rating/<gametype>/<int:page>")
def http_rating_gametype_page(gametype, page):
  return jsonify( **rating.get_list( gametype, page ) )


@app.route("/rating/<gametype>")
def http_rating_gametype(gametype):
  return http_rating_gametype_page( gametype, 0 )


@app.route("/export_rating/<frmt>/<gametype>")
def http_export_rating_format_gametype(frmt, gametype):
  frmt = frmt.lower()
  if frmt == "json":
    return jsonify( **rating.export( gametype ) )
  elif frmt == "csv":
    data = rating.export( gametype )
    if data['ok'] == False:
      return "Error: " + data['message'], 400

    result = ""
    
    for row in data["response"]:
      result += ";".join([ row["name"], str(row["rating"]), str(row["n"]), 'http://qlstats.net/player/' + row["_id"] ]) + "\n"

    response = make_response(result)
    response.headers["Content-Disposition"] = "attachment; filename=" + gametype + "_ratings.csv"
    response.headers["Content-Type"]        = "text/csv"
    return response
  else:
    return "Error: invalid format: " + frmt, 400


@app.route("/scoreboard/<match_id>")
def http_scoreboard_match_id(match_id):
  try:
    if len(match_id) != len('12345678-1234-5678-1234-567812345678'):
      raise ValueError()
    UUID(match_id)
  except ValueError:
    return jsonify(ok=False, message="invalid match_id")

  return jsonify(**rating.get_scoreboard(match_id))


@app.route("/last_matches")
@app.route("/last_matches/<gametype>")
@app.route("/last_matches/<gametype>/<int:page>")
def http_last_matches(gametype = None, page = 0):
  return jsonify(**rating.get_last_matches( gametype, page ))


@app.route("/stats/submit", methods=["POST"])
def http_stats_submit():
  # https://github.com/PredatH0r/XonStat/blob/cfeae1b0c35c48a9f14afa98717c39aa100cde59/feeder/feeder.node.js#L989
  if request.headers.get("X-D0-Blind-Id-Detached-Signature") != "dummy":
    print(request.remote_addr + ": signature header invalid or not found", file=sys.stderr)
    return jsonify(ok=False, message="signature header invalid or not found"), 403

  if request.remote_addr not in ['::ffff:127.0.0.1', '::1', '127.0.0.1']:
    print(request.remote_addr + ": non-loopback requests are not allowed", file=sys.stderr)
    return jsonify(ok=False, message="non-loopback requests are not allowed"), 403

  result = rating.submit_match(request.data.decode('utf-8'))
  if result["ok"] == False:
    print(result["match_id"] + ": " + result["message"], file=sys.stderr)
    if "match_already_exists" in result:
      return jsonify(**result), 409
    else:
      return jsonify(**result), 422
  else:
    print(result["match_id"] + ": " + result["message"])
    if cfg['run_post_process'] == False:
      result["ok"] = False
      return jsonify(**result), 202
    else:
      return jsonify(**result), 200


if __name__ == "__main__":
    app.run( host = "0.0.0.0", port = cfg['httpd_port'], threaded = True)
