import json


inp = input()
while inp != "exit":
    with open("data.txt", "r", encoding="utf8") as f:
        data = json.loads(f.read())
    cmd = inp.split()[0]
    req_name = inp.split()[1]
    for k, v in data.items():
        if req_name in v["name"] or req_name == "@a":
            if cmd == "ban":
                data[k]["banned"] = True
                print("banned " + v["name"])
            elif cmd == "unban":
                data[k]["banned"] = False
                print("unbanned " + v["name"])
            elif cmd == "info":
                for j, i in v.items():
                    print(j + ": " + str(i))
            elif cmd == "list":
                print(v["name"])
            elif cmd == "set_money":
                data[k]["money"] = float(inp.split()[2])
                print("updated money x64", data[k]["money"])
    with open("data.txt", "w", encoding="utf8") as f:
        f.write(json.dumps(data))
    inp = input()
