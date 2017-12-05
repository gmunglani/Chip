import ConfigParser

def createConfig(path):
    config = ConfigParser.ConfigParser()
    config.add_section("Parameters")
    config.set("Parameters", "Radius", "2.26")
    config.set("Parameters", "Thickness", "0.2")
    config.set("Parameters", "Stretch", "1.317")
    config.set("Parameters", "Stiffness", "2.34")

    with open(path, "w") as config_file:
        config.write(config_file)
        

if __name__ == "__main__":
    path = "config.ini"
    createConfig(path)
