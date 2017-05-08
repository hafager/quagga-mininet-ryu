import subprocess
import sys
import telnetlib

DAEMON = "ospfd"

SHOW_IP_OSPF = "show ip ospf"
SHOW_IP_OSPF_DATABASE = "show ip ospf database"
SHOW_IP_OSPF_ROUTE = "show ip ospf route"
SHOW_IP_OSPF_DATABASE_ROUTER = "show ip ospf database router %s"
SHOW_IP_OSPF_DATA_NETWORK = "show ip ospf data network"

OSPF_AREA = "0.0.0.3"
HOST = "10.0.3.254"
PORT = 2604
user = "r3"
password = "zebra"


class ospf_api:

    def __init__(self):
        self.DAEMON = "ospfd"
        self.router_id = self.__fetch_router_id()
        self.attached_routers = {}

        self.fetch_connected_routers()
        self.fetch_router_routes()


    def list_attached_routers(self):
        return self.attached_routers.keys()

    def __fetch_router_id(self):
        output = self.__vtysh_command(SHOW_IP_OSPF)
        parsed_output = self.__parse_ospf(output)

        return parsed_output["Router ID"]

    def fetch_connected_routers(self):
        output = self.__vtysh_command(SHOW_IP_OSPF_DATA_NETWORK)
        parsed_output = self.__parse_ospf_data_network(output)

        for router in parsed_output['Attached Router']:
            self.attached_routers[router] = {}
        #return parsed_output['Attached Router']

    def fetch_router_routes(self):
        routers = []
        for router in self.attached_routers.keys():
            output = self.__vtysh_command(SHOW_IP_OSPF_DATABASE_ROUTER % router)

            parsed_output = self.__parse_ospf_route(output)
            routers.append(parsed_output)
        print len(routers)

        #return parsed_output

    def __vtysh_command(self, command):
        a = subprocess.Popen(["sudo", "vtysh", "-d", self.DAEMON, "-c", command], stdout=subprocess.PIPE)
        output = a.stdout.read()
        return output

    def __telnet_command(self, command):
        tn = telnetlib.Telnet(HOST, PORT)

        tn.read_until("Password: ")
        tn.write(password + '\n')

        tn.write(command)

        tn.read_until(command)
        output = tn.read_all()
        tn.close()
        return output


    def __parse_ospf_data_network(self, data):
        # print data
        parsed_data = {"Attached Router": []}
        for line in data.splitlines():
            # print line
            if line and ':' in line:
                line = line.split(':')
                line = [x.strip() for x in line]
                if len(line) == 2:
                    if line[0] == "Attached Router":

                        if not line[1] == self.router_id:
                            temp_attached = parsed_data["Attached Router"]
                            temp_attached.append(line[1])
                            parsed_data["Attached Router"] = temp_attached
                    else:
                        parsed_data[line[0]] = line[1]
                elif len(line) > 2:
                    parsed_data[line[0]] = line[1:]

        return parsed_data

    def __parse_ospf_route(self, data):
        parsed_data = {}
        temp_data = [x.strip() for x in data.splitlines() if x]

        parsing_links = False
        number_of_links = 0
        for line in temp_data:
            if ":" in line:
                line = line.split(':')
                if len(line) == 2:

                    if not parsing_links:
                        parsed_data[line[0]] = line[1].strip()
                        if line[0] == "Number of Links":
                            number_of_links = int(line[1])
                            parsing_links = True
                            parsed_data["Links"] = {i: {} for i in range(int(line[1]))}
                    else:
                        if line[0] == "Link connected to":
                            number_of_links -= 1
                        parsed_data["Links"][number_of_links][line[0]] = line[1].strip()
        return parsed_data

    def __parse_ospf(self, data):
        temp = data.split('\n')
        parsed_data = {"Router ID": temp[0].split()[-1]}
        return parsed_data



if __name__ == '__main__':

    ospf = ospf_api()

    print ospf.router_id
    print ospf.list_attached_routers()
