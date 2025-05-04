import sys
sys.path.append('/home/pi/Desktop/anti-iha_haberlesme')
sys.path.append('/home/pi/Desktop/anti-iha_haberlesme/venv/Lib/site-packages/')
"""
PipeOutput class
"""

class PipeOutput():

    def __init__(self, hub_pipe_connector, targets, msg_filter, targets_to_be_filtered):
        """
        Constructor of PipeOutput.

        :param HubPipelineConnector hub_pipe_connector: connector object to connect related
                                                        callback function and output (targets)
                                                        objects.
        :param HubElement targets: Message targets.
        """
        self.time_step = 0.01

        self.connector = hub_pipe_connector
        self.targets = targets

        self.msg_filter = msg_filter
        self.targets_to_be_filtered = targets_to_be_filtered


        self.connector.bindToNewMsgs(self.sendNewMsgsToTargets)

    def sendNewMsgsToTargets(self, newMsgs):
        """
        Send new messages to the available targets.

        :param newMsgs: Message obtained from source.
        """
        if newMsgs != None:

            if newMsgs:
                for msg in newMsgs:
                    # print("----------------------")
                    # print('> ' + str(msg))
                    mtype = msg.get_type()

                    # don't pass along bad data
                    if (mtype != 'BAD_DATA'):
                        mbuf = msg.get_msgbuf()

                        for target in self.targets:

                            if True:

                                # if target.name == "wifi":
                                #     print("output_wifi", newMsgs)
                                if target.limiter.buff_size_limit != None:

                                    temp = target.limiter.buff + mbuf
                                    if sys.getsizeof(temp) - 33 < target.limiter.buff_size_limit and sys.getsizeof(mbuf) - 33 < target.limiter.radio_buff_size_limit:
                                        #33 çıkarılınca doğru değer bulunur

                                        # Filter messages based on target
                                        if (mtype not in self.msg_filter):
                                            #target.connection.write(mbuf)
                                            target.limiter.buff = target.limiter.buff + mbuf
                                            # if target.name == "ground_radio1":
                                            #     print("-*-to_air: ",target.limiter.buff)
                                        else:
                                            if (target not in self.targets_to_be_filtered):
                                                #target.connection.write(mbuf)
                                                target.limiter.buff = target.limiter.buff + mbuf
                                                # if target.name == "ground_radio1":
                                                #     print("-*-to_air: ",target.limiter.buff)
                                            else:
                                                # print(" -> to Target " + str(target.name) + "--> MESSAGE: " + str(mtype) +
                                                #       " !!!! BLOCKED !!!!")
                                                continue
                                else:

                                    if (mtype not in self.msg_filter):

                                        target.connection.write(mbuf)
                                    else:
                                        if (target not in self.targets_to_be_filtered):

                                            target.connection.write(mbuf)
                                        else:
                                            # print(" -> to Target " + str(target.name) + "--> MESSAGE: " + str(mtype) +
                                            #       " !!!! BLOCKED !!!!")
                                            continue

            self.connector.newMsgs = None
