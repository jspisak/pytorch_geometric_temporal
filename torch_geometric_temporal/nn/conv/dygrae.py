import torch
from torch.nn import LSTM
from torch_geometric.nn import GatedGraphConv

class DyGrEncoder(torch.nn.Module):
    r"""An implementation of the integrated Gated Graph Convolution Long Short
    Term Memory Layer. For details see this paper: `"Predictive Temporal Embedding
    of Dynamic Graphs." <https://ieeexplore.ieee.org/document/9073186>`_

    Args:
        conv_out_channels (int): Number of convolution channels.
        conv_num_layers (int): Number of Gated Graph Convolutions.
        conv_aggr (str): Aggregation scheme to use - one of add/sum/mean.
        lstm_out_channels (int): Number of LSTM channels.
        lstm_num_layers (int): Number of LSTM cells.
    """
    def __init__(self, conv_out_channels: int, conv_num_layers: int, conv_aggr: str,
                 lstm_out_channels: int, lstm_num_layers: int):
        super(DyGrEncoder, self).__init__()

        self.conv_out_channels = conv_out_channels
        self.conv_num_layers = conv_num_layers
        self.conv_aggr = conv_aggr
        self.lstm_out_channels = lstm_out_channels
        self.lstm_num_layers = lstm_num_layers
        self._create_layers()


    def _create_layers(self):
        self.conv_layer = GatedGraphConv(out_channels = self.conv_out_channels,
                                         num_layers = self.conv_num_layers,
                                         aggr = self.conv_aggr,
                                         bias = True)

        self.recurrent_layer = LSTM(input_size = self.conv_out_channels,
                                    hidden_size = self.lstm_out_channels,
                                    num_layers = self.lstm_num_layers)


    def forward(self, X: torch.FloatTensor, edge_index: torch.LongTensor,
                edge_weight: torch.FloatTensor=None, H: torch.FloatTensor=None, C: torch.FloatTensor=None):
        """
        Making a forward pass. If the hidden state and cell state matrices are 
        not present when the forward pass is called these are initialized with zeros.

        Arg types:
            * **X** *(PyTorch Float Tensor)* - Node features.
            * **edge_index** *(PyTorch Long Tensor)* - Graph edge indices.
            * **edge_weight** *(PyTorch Float Tensor)* - Edge weight vector (optional).
            * **H** *(PyTorch Float Tensor)* - Hidden state matrix for all nodes (optional).
            * **C** *(PyTorch Float Tensor)* - Cell state matrix for all nodes (optional).

        Return types:
            * **H_tilde** *(PyTorch Float Tensor)* - Output matrix for all nodes.
            * **H** *(PyTorch Float Tensor)* - Hidden state matrix for all nodes.
            * **C** *(PyTorch Float Tensor)* - Cell state matrix for all nodes.
        """
        H_tilde = self.conv_layer(X, edge_index, edge_weight)
        H_tilde = H_tilde[None, :, :]
        if H is None and C is None: 
            H_tilde, (H, C) = self.recurrent_layer(H_tilde)
        elif H is not None and C is not None: 
            H = H[None, :, :]
            C = C[None, :, :]
            H_tilde, (H, C) = self.recurrent_layer(H_tilde, (H, C))
        H_tilde = H_tilde.squeeze()
        H = H.squeeze()
        C = C.squeeze()
        return H_tilde, H, C
