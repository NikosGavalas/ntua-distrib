# Κατανεμημένα Συστήματα

## Αναφορά εξαμηνιαίας εργασίας

### Ομάδα 34

| | |
| -- | -- | 
| Γαβαλάς Νίκος | 03113121 |
| Καραμέρης Μάρκος | 03113148 |

## Περιγραφή

### Απαιτήσεις

### Υλοποίηση

python, heartbeats, buffering

 <!-- Προβλήματα - Λύσεις -->
### Σχεδιαστικές Αποφάσεις

select syscall, client messages

## Πειράματα

### Deployment

### Πείραμα 1: Απόδοση του συστήματος 
btw mporoume na xrhsimop... cause docker -> ola to idio systime
#### FIFO Ordering

` python3 tests.py 5 46663 1`

##### client0

recv_end for:
| c0 | c1 | c2 | c3 | c4 |
| -- | -- | -- | -- | -- |
| 1520863279.381437 | 1520863279.344317 |  1520863279.380326  | 1520863279.447183 | 1520863279.398963 | 

| send_start | send_end | recv_end | elapsed (recv_end - send_start) |
| -- | -- | -- |
| 1520863279.364653 | 1520863279.382046 | 0.017394 |

rerun:

start: 1520864763.220646
end: 1520864763.239089
elapsed: 0.018443

message 10e Beware of the Leopard from client4 received at 1520864763.802138
message 10d Forty-two from client3 received at 1520864763.317927
message 10a I'd far rather be happy than right any day. from client0 received at 1520864763.238586
message 10c Doesn't matter! from client2 received at 1520864763.233414
message 10b There is an answer? from client1 received at 1520864763.195053

##### client1

| send_start | recv_end | elapsed |

start: 1520864763.185815
end: 1520864763.195127
elapsed: 0.009312

message 10e Beware of the Leopard from client4 received at 1520864763.801671
message 10d Forty-two from client3 received at 1520864763.317673
message 10a I'd far rather be happy than right any day. from client0 received at 1520864763.237956
message 10c Doesn't matter! from client2 received at 1520864763.232598
message 10b There is an answer? from client1 received at 1520864763.194553

##### client2

| send_start | recv_end | elapsed |

start: 1520864763.224812
end: 1520864763.232978
elapsed: 0.008166

message 10e Beware of the Leopard from client4 received at 1520864763.801829
message 10d Forty-two from client3 received at 1520864763.317707
message 10a I'd far rather be happy than right any day. from client0 received at 1520864763.238106
message 10c Doesn't matter! from client2 received at 1520864763.232475
message 10b There is an answer? from client1 received at 1520864763.194957

##### client3

| send_start | recv_end | elapsed |

start: 1520864763.308182
end: 1520864763.318171
elapsed: 0.009989

message 10e Beware of the Leopard from client4 received at 1520864763.801995
message 10d Forty-two from client3 received at 1520864763.317729
message 10a I'd far rather be happy than right any day. from client0 received at 1520864763.238746
message 10c Doesn't matter! from client2 received at 1520864763.232818
message 10b There is an answer? from client1 received at 1520864763.195013

##### client4

| send_start | recv_end | elapsed |

start: 1520864763.787793
end: 1520864763.801837
elapsed: 0.014044

message 10e Beware of the Leopard from client4 received at 1520864763.801871
message 1e But the plans were on display from client4 received at 1520864763.791658
message 10a I'd far rather be happy than right any day. from client0 received at 1520864763.238704
message 10c Doesn't matter! from client2 received at 1520864763.232801
message 10b There is an answer? from client1 received at 1520864763.195222


#### FIFO & Total Ordering



### Πείραμα 2: Κλιμακωσιμότητα του συστήματος