# Description:
#  Dikhao - A quick view of all related EC2 & Route53 resources.
#
# Commands:
#   hubot (dikhao|batao) search_item - A quick view of all related EC2 & Route53 resources.
#
# Author:
#   Rohit Gupta

module.exports = (robot) ->
  url = "http://dikhao.herokuapp.com"
  commandName = 'dikhao'

  robot.respond /(dikhao|batao) (.*)/i, (msg) ->
    search_item = msg.match[2]

    msg.http("#{url}/lookup/#{search_item}").post() (err, res, body) ->
        if not err and res.statusCode is 200
          robot.logger.info "#{msg.match[0]}, search_item: #{search_item}"
          msg.send "/quote #{body}"
        else
          robot.logger.error "#{res.statusCode} error at  #{url}", err, res
          msg.send "[ERROR] Sorry, but I was unable to fetch details for you."
