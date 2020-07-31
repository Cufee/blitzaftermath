from operator import itemgetter
string = """```
RGN       124
-MM       118
PURPL      84
GMA        57
RIVAL      40
BZO        32
PRAMO      29
PNCR       26
SYKO-      25
NERFD      24
GLOX       23
UNI0N      23
YODA_      22
O_C_S      22
GOSU       19
CALI       19
-JJ        17
STORM      16
-RVG-      15
_NUKE      15
BHOTT      15
V1CE       14
BETTA      14
_V_        14
PEARL      13
DOOMD      13
CLEAR      13
UN10N      13
BRO3       12
B-OP       11
_STR8      11
DEF_6      11
--R--      11
-ZER0      10
---        10
-MI6-      10
HELLD      10
--7--      10
HATED      10
WEAK       10
-INQ-       9
TXSRG       9
2DACR       9
-BA-        9
CARRY       8
DOOBY       8
ASTER       8
CRUEL       8
-GP-        8
BTP         8```
"""

string = string.strip().replace('```', '').split('\n')
new_list = []
for s in string:
    s_list = s.split(' ')
    for sl in s_list:
        sl.strip()

    new_list += s_list
for item in new_list:
    index = new_list.index(item)
    if item == '' or item == ' ':
        new_list.pop(index)

it = iter(new_list[0:20])

final = zip(it, it)
print(list(final))
