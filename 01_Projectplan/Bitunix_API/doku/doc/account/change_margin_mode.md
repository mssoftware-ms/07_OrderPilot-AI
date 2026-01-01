

# Change Margin Mode ​

Rate Limit: 10 req/sec/uid

### Description ​

This interface cannot be used when the users have an open position or an order

### HTTP Request ​

* POST /api/v1/futures/account/change_margin_mode


### Request Parameters ​



| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| marginMode | string | true | Margin ModeISOLATIONCROSS |
| symbol | string | true | Trading pair |
| marginCoin | string | true | Margin coin |

Request Examplebash
```
curl -X 'POST'  --location 'https://fapi.bitunix.com/api/v1/futures/account/change_margin_mode' \
   -H "api-key:*******" \
   -H "sign:*" \
   -H "nonce:your-nonce" \
   -H "timestamp:1659076670000" \
   -H "language:en-US" \
   -H "Content-Type: application/json" \
 --data '{"marginMode":"ISOLATION","symbol":"BTCUSDT","marginCoin":"USDT"}'
```


### Response Parameters ​



| Parameter | Type | Description |
| --- | --- | --- |
| marginMode | string | Margin ModeISOLATIONCROSS |
| symbol | string | Trading pair |
| marginCoin | string | Margin coin |

Response Examplejson
```
{"code":0,"data":[{"positionMode":"ISOLATION"}],"msg":"Success"}
```
