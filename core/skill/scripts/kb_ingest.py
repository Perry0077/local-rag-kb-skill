#!/usr/bin/env python3
from _shared import bootstrap_runtime_path

bootstrap_runtime_path()

from local_rag_kb.commands.ingest import main


if __name__ == "__main__":
    main()
