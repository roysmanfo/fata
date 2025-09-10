import os


class LogManager:
    """
    LogManager handles log reading and writing from the 
    Engine and the web interface. 
    
    Reading and writing happens thanks to pipes which allow for safer
    access control
    """

    read_fd: int = -1
    write_fd: int = -1

    @staticmethod
    def init(force: bool = False):
        if LogManager.read_fd != -1 and LogManager.write_fd != -1:
            if not force:
                raise RuntimeError("unable to create new log pipes (file already exists)")
            LogManager.close()

        # create (or recreate) pipes 
        r, w = os.pipe()
        LogManager.read_fd = r
        LogManager.write_fd = w

    @staticmethod
    def read_pipe():
        return open(LogManager.read_fd, 'rt', encoding='utf-8')

    @staticmethod
    def write_pipe():
        return open(LogManager.write, 'wt', encoding='utf-8')

    @staticmethod
    def close():
        """
        Close all pipes
        """
        os.close(LogManager.read_fd)
        os.close(LogManager.write_fd)