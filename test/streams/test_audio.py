# Built-in Imports
import os
import pathlib
import time
import datetime

# Third-party
import numpy as np
import pytest
import pyaudio

# Internal Imports
import chimerapy.engine as cpe
from chimerapy.engine.node.record_service.records.audio_record import AudioRecord
from chimerapy.engine.node.record_service.entry import AudioEntry
from chimerapy.engine.node.events import RecordEvent
from chimerapy.engine.networking.async_loop_thread import AsyncLoopThread
from chimerapy.engine.eventbus import EventBus, Event

from .data_nodes import AudioNode

logger = cpe._logger.getLogger("chimerapy-engine")

# Constants
CWD = pathlib.Path(os.path.abspath(__file__)).parent.parent
TEST_DATA_DIR = CWD / "data"
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 2


@pytest.fixture
def audio_node():

    # Create a node
    an = AudioNode("an", CHUNK, CHANNELS, FORMAT, RATE)

    return an


def test_audio_record():

    # Check that the audio was created
    expected_audio_path = TEST_DATA_DIR / "test.wav"
    try:
        os.remove(expected_audio_path)
    except FileNotFoundError:
        ...

    # Create the record
    ar = AudioRecord(dir=TEST_DATA_DIR, name="test", start_time=datetime.datetime.now())

    # Write to audio file
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = (np.random.rand(CHUNK) * 2 - 1) * (i * 0.1)
        audio_entry = AudioEntry(
            name="test", data=data, channels=CHANNELS, format=FORMAT, rate=RATE
        )
        ar.write(audio_entry)

    assert expected_audio_path.exists()


def test_node_save_audio_stream(audio_node):

    # Event Loop
    thread = AsyncLoopThread()
    thread.start()
    eventbus = EventBus(thread=thread)

    # Check that the audio was created
    expected_audio_path = audio_node.state.logdir / "test" / "test.wav"
    try:
        os.remove(expected_audio_path)
    except FileNotFoundError:
        ...

    # Stream
    audio_node.run(blocking=False, eventbus=eventbus)

    # Wait to generate files
    eventbus.send(Event("start")).result()
    logger.debug("Finish start")
    eventbus.send(Event("record", RecordEvent("test"))).result()
    logger.debug("Finish record")
    time.sleep(3)
    eventbus.send(Event("stop")).result()
    logger.debug("Finish stop")
    eventbus.send(Event("collect")).result()
    logger.debug("Finish collect")

    audio_node.shutdown()

    # Check that the audio was created
    assert expected_audio_path.exists()
