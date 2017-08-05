#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from bot import ClosetBot

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def main():
    cb = ClosetBot()
    cb.run()

if __name__ == "__main__":
    exit(main())
