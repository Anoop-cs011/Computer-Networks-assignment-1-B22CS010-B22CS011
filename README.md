# Computer-Networks-assignment-1-B22CS010-B22CS011
Implemented a gossip protocol over a peer-to-peer network such that the degree distribution of the peer nodes follows power law.<br />
![degreeDistributionLogLogScale](https://github.com/user-attachments/assets/83bd6697-f35f-49e4-8187-f9b29415bdff)

## Steps to Run the Code

1. **Set up the config file**: Create a `config.csv` file with the IP addresses and port numbers of the seed nodes.
2. **Set up the peers file**: Create a `peers.csv` file with the IP addresses and port numbers of the peer nodes.
3. **Run the codes**: Execute the `seed.py` & `peer.py` script on  on seperate terminals.

   ```bash
   python seed.py
   ```
   ```bash
   python peer.py
   ```

4. Once there does not seem to be any change in terminal outputs, run networPlot.py to check degree distribution
   ```bash
   python networkPlot.py
   ```
   
**Switch the main function in seed.py and peer.py to run on seperate machines** (dont forget to update the config file):<br />
![image](https://github.com/user-attachments/assets/be124108-e79c-4b08-aee4-0f4f855c14f1)
