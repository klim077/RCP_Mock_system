const express = require("express");
const http = require('http');
const redis = require('redis');
const expressApp = express();
const server = http.createServer(expressApp);
const io = require('socket.io')(server, {
    pingInterval: 10000,
    pingTimeout: 5000
});
const config = require('config');
const log = require('gelf-pro');
const HTTP_PORT = 80;

// Graylog settings
let graylog_ip = config.get('graylog.ip');
let graylog_port = config.get('graylog.port');

log.setConfig({
    fields: {project: "SmartGym", repo: "smartgym-backend"}, 
    adapterOptions: {host: graylog_ip, port: graylog_port},
    broadcast: [
        function (message) { // broadcasting to console
          console[message.level > 3 ? 'log' : 'error'](message.short_message, message);
        }
      ]
});

// Socket IO call backs
io.on("connection", (client) => {    
    new Socket(client);
});

/**
 * This class is to used to bridge the incoming socket connection to a 
 * redis client connection
 */
class Socket {

    constructor(socketClient) {

        /** For socket io */
        this.socketClient = socketClient;
        log.info("new socketio client connected... ");        

        // when the socketClient emits or 'mobileConnected', this listens and executes
	    this.socketClient.on('mobileConnected', this.onMobileConnected.bind(this));

        /** For redis */
        // a redis client is created and connects
	    this.redisClient = redis.createClient(config.get('redis.port'), config.get('redis.ip'));

        this.redisClient.on('connect', function() {
            log.info('Redis client connected ');
        });
        this.redisClient.on('error', function (err) {
            log.error('Redis client something went wrong ' + err);
        });
        this.redisClient.on('message', function (channel, message) {
            if(message.hasOwnProperty("message")){ // after saving workout
                message = message
            }
            log.info('Redis message received...');
            socketClient.emit('updatemessage', message)
        });
    }

}

Socket.prototype.onMobileConnected = function (msg) {

    // when mobile is connected to server, the user is already logged in (channel)
    // we can then subscribe to that user channel
    let jsonReceived = {};
    try {
        jsonReceived = JSON.parse(msg);
    } catch(e) {
        log.error('JSON parsing error' + "\n" + e);
    }
    let jsonString = JSON.stringify(jsonReceived);
    const fromServer = "From Mobile received @ " + (new Date());
    log.info('SocketIO server received: ' + fromServer);

    // subscribe to redis for this user channel
    if(typeof jsonReceived["channel"]  !== 'undefined') {
        this.redisClient.subscribe(jsonReceived["channel"]);
    }

    // emit back to socket io client that a user have joined and ack
    this.socketClient.emit("ackmessage", fromServer);
}

// export the server so it can be easily called for testing
exports.server = server.listen(HTTP_PORT, () => {
    log.info('socketio server started at port ' + HTTP_PORT);
});
