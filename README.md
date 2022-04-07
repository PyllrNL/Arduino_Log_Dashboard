# Logging Dashboard

## Upcoming Changes

### Websocket API

*Note: The upcoming changes are plannned for v0.2.0*

The websocket api uses msgpack for communication and encodes the message
in base64 to send it through the websocket.

The API uses two different data categories, and a response type to communicate.
Every data transmission has a corresponding response from the receiver, and in
order to avoid confusion to the matching of data transmissions and responses
any participant of a websocket is only allowed to send one type at a time.

#### Responses

A response takes the form of:

```
[ 
  <uint8_t> 0,
  <uint16_t><response_code>
]
```

The api uses the first element in the array to determine the data category.
The first 256 error codes are reserved for general use and likely will be
all you need.

The response codes are:

| Error Code | Meaning |
|:----------:|:-------:|
| 0 | The previous data transmission was well received |
| 1 | PING event response |
| 2 | General error message, used if participant doesn't know what went wrong.|

#### Events

An event takes the form of:

```
[ 
  <uint8_t> 1, 
  <uint16_t> <event code>,
  <int64_t> <timestamp>,
  <any valid msgpack>
]
```

A event transmission is just a tad more involved than the response transmission.
It consists of the event identifier as the first element, an event code as
the second, a timestamp as the third element and any valid base msgpack object
as the fourth element. Events are designed for any type of data transmission
that is not consistent in time, I.E. a button being pressed or a watchdog
resetting.

Just like response codes, the first 256 event codes are reserved for future use

The event codes are:

| Event code | Meaning |
|:----------:|:-------:|
| 0 | PING, used to determine the status of websocket connection |

#### Data streams

A data stream transmission takes the form of:

```
[
    <uint8_t> 2,
    <uint8_t> stream_num,
    <uint8_t> temporal specification,
    <int64_t> timestamp,
    <int64_t> timedelta,
    [
        [{ <int64_t> timestamp|timedelta }],
        [ n data samples of any single type ]
    ]
]
```

the data transmission type is arguably the most complex category of the three.
One thing that adds complexity is the `temporal speficiation`. the
`temporal specification` allows the sender to use different types of timing
for different streams.

##### Temporal speficiation

1. Full Frame

With a full frame, each data point of the stream has a corresponding timestamp
in the optional first element of the data array. Because timestamps use 64-bit
signed integers, it requires a lot of data and is not recommended for large
datasets. both the global `timestamp` and `timedelta` can be set to any
number and will be ignored.

2. Full deltaframe

A full deltaframe is similair to the `full frame` with the exception that
instead of sending timestamps for each data point, it sends a delta per data
point. This specification requires the global `timestamp` to be set.

3. Interframe

An interframe uses the global `timestamp` and `timedelta` values for the data
points, the receiver of the transmission will use the `timestamp` for the
first value in the dataset and add the `timedelta` for each subsequent data point.

4. deltaframe

The normal deltaframe is mostly the same as the interframe, with the exception
that it does not send a global `timestamp` and uses the last known timestamp
as the basis for calculating the new `timestamps`.

<!--
### Rest API

*Note: The upcoming changes are planned for v0.3.0*

### Front-End

*Note: The upcoming changes are planned for v0.4.0*

### Database

*Note: The upcoming changes are planned for v0.5.0*

## Possible additional features in the future

### Data stream filters

### Rewriting the server backend for higher loads
-->
