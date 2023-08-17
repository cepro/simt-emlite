import logging

FORMAT = '%(asctime)s %(levelname)s %(name)s[%(process)d]: %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

Logger = logging.Logger  # re-export


def get_logger(name: str):
    # Would like to set the following to get the above FORMAT working
    # however when I do i get duplicates but only logging handler ...

    # handler = logging.StreamHandler()
    # handler.setFormatter(logging.Formatter(FORMAT))

    # logger = logging.getLogger(module_name)
    # logger.addHandler(handler)

    return logging.getLogger(name)
