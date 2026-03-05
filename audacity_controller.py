# Audacity controller
#
# Patrick Dumais Jan 2026
import os

EOL = '\n'

class AudacityPipeController:
    def __init__(self):

        self.toname = '/tmp/audacity_script_pipe.to.' + str(os.getuid())
        self.fromname = '/tmp/audacity_script_pipe.from.' + str(os.getuid())
        to_exists = 0
        from_exists = 0

        print("Write to  \"" + self.toname + "\"")
        if not os.path.exists(self.toname):
            print(" ..does not exist.  Ensure Audacity is running with mod-script-pipe.")
        else:
            to_exists = 1

        print("Read from \"" + self.fromname + "\"")
        if not os.path.exists(self.fromname):
            print(" ..does not exist.  Ensure Audacity is running with mod-script-pipe.")
        else:
            from_exists = 1

        if to_exists and from_exists:
            print("-- Both pipes exist.  Good.")
            self.tofile = open(self.toname, 'wt')
            print("-- File to write to has been opened")
            self.fromfile = open(self.fromname, 'rt')
            print("-- File to read from has now been opened too")

            print('Pipes appear fully functional.')


    def sendCommand(self, command):
        print("Send: >>> \n" + command)
        self.tofile.write(command + EOL)
        self.tofile.flush()


    def getResponse(self):
        result = ''
        line = ''
        while line != '\n':
            result += line
            line = self.fromfile.readline()
        # print(" I read line:["+line+"]")
        return result


    def doCommand(self, command):
        self.sendCommand(command)
        response = self.getResponse()
        print("Rcvd: <<< \n" + response)
        return response


    def quickTest(self):
        #self.doCommand('Help: Command=Help')
        self.doCommand('Help: Command="GetInfo"')
        # do( 'SetPreference: Name=GUI/Theme Value=classic Reload=1' )

    def record(self):
        self.doCommand('Record2ndChoice')

    def stop(self):
        self.doCommand('stop:')

    # works without dialog using target with .mp3 extension (ExportMP3: does trigger a dialog)
    def saveTo(self, savetopath):
        #self.doCommand('ExportMP3: Filename=/home/patrick/Music/recording.mp3')
        self.doCommand('SelectAll')
        self.doCommand(f'Export2: Filename=\"{savetopath}\"')

    # clear the existing recording so we can start a new one
    def clearTrack(self):
        self.doCommand('SelectAll:')
        self.doCommand('RemoveTracks:')

# Test routine if run as main
if __name__ == "__main__":
    audacity = AudacityPipeController()
    #audacity.quickTest()
    #audacity.record
    #audacity.saveTo()
    audacity.stop()