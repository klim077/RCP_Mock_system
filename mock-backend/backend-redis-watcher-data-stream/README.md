# SmartGym Backend Redis Watcher[data_stream]

This service uses [Redis Keyspace Notifications](https://redis.io/topics/notifications) to subscribe to changes to the `data_stream` key in Redis database.

Whenever a change is made to the `data_stream` key, this service checks is the `user` key is set. If so, publishes the `uuid` to the channel named with `user` value.
