
def pad(input_bytes, block_size):
    padding = block_size - (len(input_bytes) % block_size)
    return input_bytes + bytes([padding] * padding)

def unpad(input_bytes, block_size):
    input_length = len(input_bytes)
    padding_length = int(input_bytes[-1])
    if padding_length > block_size:
        raise ValueError('Input is not padded or padding is corrupt')
    message_length = input_length - padding_length
    return input_bytes[:message_length]
