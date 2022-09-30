'use strict'

var chai = require('chai');
var chaiString = require('chai-string');
chai.use(chaiString);
var expect = chai.expect;
var redis = require('redis')
var redisMock = require('redis-mock');
var sinon = require('sinon');
var server = require('../index');
var io = require('socket.io-client');
var ioOptions = { 
  transports: ['websocket'], forceNew: true, reconnection: false
};
var testMsg = JSON.stringify({channel: 'HelloWorld', machineIDreps: 1});
var sender;


describe('SocketIO Events', function(){

  before(function(done){
    sinon
      .stub(redis, 'createClient')
      .callsFake(function() {
        return redisMock.createClient();
      });
    done()
  })
  after(function(done){
    server.server.close();
    done()
  })
  
  beforeEach(function(done){
    // connect one io client
    sender = io('http://localhost:80/', ioOptions)
    
    // finish beforeEach setup
    done()
  })
  afterEach(function(done){
    // disconnect io client after each test
    sender.disconnect()
    done()
  })

  describe('Message Events', function(){
    it('Clients should receive a message when the `message` event is emited.', function(done){
      sender.emit('message', testMsg)
      sender.on('ackmessage', function(msg){
        expect(msg).to.startsWith('From Gateway')
        done()
      })
    })

    it('Clients should receive a message when the `mobileConnected` event is emited.', function(done){
      sender.emit('mobileConnected', testMsg)
      sender.on('ackmessage', function(msg){
        expect(msg).to.startsWith('From Mobile')
        done()
      })
    })
  })
})