import subprocess
import sys
import telnetlib

DAEMON = "ospfd"

SHOW_IP_OSPF = "show ip ospf"
SHOW_IP_OSPF_DATABASE = "show ip ospf database"
SHOW_IP_OSPF_ROUTE = "show ip ospf route"
SHOW_IP_OSPF_DATABASE_ROUTER = "show ip ospf database router %s"
SHOW_IP_OSPF_DATA_NETWORK = "show ip ospf data network"

OSPF_AREA = "0.0.0.%s"
HOST = "10.0.%s.254"
PORT = 2604
user = "r%s"
password = "zebra"


class ospf_api:

    def __init__(self, platform_id):

        self.generate_config(platform_id)


        self.router = self._fetch_router_id()
        print 'ROUTER ID: ', self.router
        self.router["Attached Routers"] = {}

        self.fetch_connected_routers()
        self.fetch_router_routes()
        # self.test()

    def generate_config(self, platform_id):
        self.OSPF_AREA = "0.0.0.%s" % platform_id
        self.HOST = "10.0.%s.254" % platform_id
        self.PORT = 2604
        self.DAEMON = "ospfd"
        self.user = "r%s" % platform_id
        self.password = "zebra"


    def test(self):
        return self.list_attached_routers()

    def update(self):
        #self.router_id = self._fetch_router_id()
        self.fetch_connected_routers()
        self.fetch_router_routes()
        #print self._telnet_command(SHOW_IP_OSPF_DATA_NETWORK)
        print self.list_attached_routers()

    def telnet_update(self):
        a = 1

    def list_attached_routers(self):
        temp = {}
        for router in self.router["Attached Routers"]:
            if self.router["Attached Routers"][router]["Connected"]:
                temp[router] = self.router["Attached Routers"][router]
        return self.router["Attached Routers"]

    def _fetch_router_id(self):
        output = self._telnet_command(SHOW_IP_OSPF)
        parsed_output = self._parse_ospf(output)

        return parsed_output

    def fetch_connected_routers(self):
        output = self._telnet_command(SHOW_IP_OSPF_DATA_NETWORK)
        parsed_output = self._parse_ospf_data_network(output)

        # Add new routers
        for router in parsed_output['Attached Router']:
            # New router
            if router not in self.router["Attached Routers"]:
                self.router["Attached Routers"][router] = {"Connected": True}
                print "New router: ", router
            # Known router which reconencted
            elif router in self.router["Attached Routers"] and not self.router["Attached Routers"][router]["Connected"]:
                self.router["Attached Routers"][router]["Connected"] = True
                print "Router reconnected", router

        # Remove old routers
        for router in self.router["Attached Routers"]:
            if router not in parsed_output['Attached Router'] and self.router["Attached Routers"][router]["Connected"]:
                self.router["Attached Routers"][router]["Connected"] = False
                print "Router disconnected: ", router

    def fetch_router_routes(self):
        routers = []
        for router in self.router["Attached Routers"].keys():
            if self.router["Attached Routers"][router]["Connected"]:
                output = self._telnet_command(SHOW_IP_OSPF_DATABASE_ROUTER % router)

                parsed_output = self._parse_ospf_route(output)
                routers.append(parsed_output)

    def _vtysh_command(self, command):
        a = subprocess.Popen(["sudo", "vtysh", "-d", self.DAEMON, "-c", command], stdout=subprocess.PIPE)
        output = a.stdout.read()
        return output

    def _telnet_command(self, command):
        tn = telnetlib.Telnet(self.HOST, self.PORT)

        tn.read_until("Password: ")
        tn.write(self.password + '\n')

        status = tn.read_some()
        if "Password" in status:
            tn.close()
            print("Didn't have the correct password")
            return
        tn.write(command + '\n')
        print command

        output = tn.read_until('%s>' % self.user)

        tn.close()
        print "Finished telnet fetch"
        return output


    def _parse_ospf_data_network(self, data):
        parsed_data = {"Attached Router": []}
        for line in data.splitlines():
            if line and ':' in line:
                line = line.split(':')
                line = [x.strip() for x in line]
                if len(line) == 2:
                    if line[0] == "Attached Router":

                        if not line[1] == self.router["Router ID"]:
                            temp_attached = parsed_data["Attached Router"]
                            temp_attached.append(line[1])
                            parsed_data["Attached Router"] = temp_attached
                    else:
                        parsed_data[line[0]] = line[1]
                elif len(line) > 2:
                    parsed_data[line[0]] = line[1:]
        return parsed_data

    def _parse_ospf_route(self, data):
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

    def _parse_ospf(self, data):
        temp = data.split('\r\n')
        print temp
        parsed_data = {"Router ID": temp[1].split()[-1]}
        return parsed_data



if __name__ == '__main__':

    ospf = ospf_api()

    #print ospf.router_id
    #print ospf.list_attached_routers()
