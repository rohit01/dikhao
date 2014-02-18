# Description:
#  Dikhao - A quick view of all related EC2 & Route53 resources.
#
# Commands:
#   hubot (dikhao|batao) search_item - A quick view of all related EC2 & Route53 resources.
#   hubot (dekho|padho) - Sync EC2 & Route53 details into redis
#
# Author:
#   Rohit Gupta

module.exports = (robot) ->
  url = "<Application url>"

  robot.respond /(dekho|padho)/i, (msg) ->
    msg.http("#{url}/sync").post() (err, res, body) ->
        if not err and res.statusCode is 200
          robot.logger.info "#{msg.match[0]}, Response: #{body}"
          msg.send "#{body}"
        else
          robot.logger.error "#{res.statusCode} error at  #{url}", err, res
          msg.send "[ERROR] Sorry, unable to initiate sync."

  robot.respond /(dikhao|batao) (.*)/i, (msg) ->
    search_item = msg.match[2]
    msg.http("#{url}/lookup/#{search_item}").post() (err, res, body) ->
        if not err and res.statusCode is 200
          robot.logger.info "#{msg.match[0]}, search_item: #{search_item}"
          msg.send "/quote #{body}"
        else
          robot.logger.error "#{res.statusCode} error at  #{url}", err, res
          msg.send "[ERROR] Sorry, but I was unable to fetch details for you."
