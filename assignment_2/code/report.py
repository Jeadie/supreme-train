import subprocess
import os
from argparse import ArgumentParser


class ReportTesting(object):

    TESTING_CONFIG = [
        (0, 0), (0, 0.1), (0, 0.2), (0, 0.3), (0, 0.4), (0, 0.5),
        (10, 0), (20, 0), (30, 0), (40, 0), (50, 0),
        (20, 0.1), (20, 0.2), (20, 0.3), (40, 0.1), (40, 0.2), (40, 0.3)
    ]

    FILE_SIZES = ["small.txt"] # mall.txt", "medium.txt"] # , "large.txt"]
    ATTEMPT_COUNT = 3
    TIME_LOG = "testing.time.log"
    def __init__(self):
        self.results = {}

    def run(self, delay, discard_prob):
        """ Runs all combinations from the TESTING_CONFIG and FILE_SIZES.

        Returns:
        """
        for config in ReportTesting.TESTING_CONFIG:
            # delay, discard_prob = config
            print(str(delay), str(discard_prob))
            # Setup network
            # network = subprocess.Popen(["nohup", "sh",  "network.sh", str(delay), str(discard_prob)])
            print('Network Configured.')

            file_averages = []
            # Test all files three times
            for f in ReportTesting.FILE_SIZES:
                for attempt in range(ReportTesting.ATTEMPT_COUNT):
                    print(f"Running attempt: {attempt} for file {f}. Config: {config}")
                    test = subprocess.Popen(["nohup", "sh",  "testing.sh", f])
                    # sender = subprocess.Popen(["nohup", "sh",  "sender.sh", f])
                    # receiver = subprocess.Popen(["nohup", "sh", "receiver.sh", f])
                    print("Waiting...")
                    test.wait()
                    print("Sender Done")
                    # receiver.wait()
                    print("Done.\n")
                print(f"Run testing for {f}")
                with open(ReportTesting.TIME_LOG, "r") as f:
                    data = f.readlines()
                average = sum([float(d[:-1]) for d in data]) / ReportTesting.ATTEMPT_COUNT
                os.remove(ReportTesting.TIME_LOG)
                print(f"TIME: {average}")
                file_averages.append(average)
            # network.kill()
            self.results[(delay, discard_prob)] = file_averages
            return

    def save_to_csv(self, filename):
        """

        Args:
            filename:

        """
        with open(filename, "a") as f:
            for config, result in self.results.items():
                print(f"{config[0]},{config[1]},{','.join([str(r) for r in result])}")
                f.write(f"{config[0]},{config[1]},{','.join([str(r) for r in result])}\n")


def main():
    parser = ArgumentParser(description='Report')
    parser.add_argument("delay", type=int,
                        help="The max delay of a packet")
    parser.add_argument("prob", type=float, help="The probability a packet gets dropped.")
    args = parser.parse_args()

    r = ReportTesting()
    r.run(args.delay, args.prob)
    print(r.results)
    r.save_to_csv("results.csv")

if __name__ == "__main__":
    main()
