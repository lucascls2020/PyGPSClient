"""
SerialHandler class for PyGPSClient application

This handles all the serial i/o , threaded read process and direction to
the appropriate protocol handler

Created on 16 Sep 2020

:author: semuadmin
:copyright: SEMU Consulting © 2020
:license: BSD 3-Clause
"""

from io import BufferedReader
from threading import Thread
from serial import Serial, SerialException, SerialTimeoutException
from pyubx2 import UBXReader, UBXParseError, protocol
from pynmeagps import NMEAParseError
import pyubx2.ubxtypes_core as ubt
from pygpsclient.globals import (
    CONNECTED,
    CONNECTED_FILE,
    DISCONNECTED,
    QUITONERRORDEFAULT,
)
from pygpsclient.strings import NOTCONN, SEROPENERROR, FILEOPENERROR, ENDOFFILE


class SerialHandler:
    """
    Serial handler class.
    """

    def __init__(self, app):
        """
        Constructor.

        :param Frame app: reference to main tkinter application

        """

        self.__app = app  # Reference to main application class
        self.__master = self.__app.get_master()  # Reference to root class (Tk)

        self._serial_object = None
        self._serial_buffer = None
        self._serial_thread = None
        self._file_thread = None
        self._connected = False
        self._reader = None
        self._reading = False

    def __del__(self):
        """
        Destructor.
        """

        if self._serial_thread is not None:
            self._reading = False
            self._serial_thread = None
            self.disconnect()

    def connect(self):
        """
        Open serial connection.
        """

        serial_settings = self.__app.frm_settings.serial_settings()
        if serial_settings.status == 3:  # NOPORTS
            return

        try:

            self._serial_object = Serial(
                serial_settings.port,
                serial_settings.bpsrate,
                bytesize=serial_settings.databits,
                stopbits=serial_settings.stopbits,
                parity=serial_settings.parity,
                xonxoff=serial_settings.xonxoff,
                rtscts=serial_settings.rtscts,
                timeout=serial_settings.timeout,
            )
            self._serial_buffer = BufferedReader(self._serial_object)
            msg = (
                f"{serial_settings.port}:{serial_settings.port_desc}"
                + f"@ {str(serial_settings.bpsrate)}"
            )
            self.connect_stream(self._serial_buffer, CONNECTED, msg)

        except (IOError, SerialException, SerialTimeoutException) as err:
            self._connected = False
            self.__app.set_connection(
                (
                    f"{serial_settings.port}:{serial_settings.port_desc} "
                    + f"@ {str(serial_settings.bpsrate)}"
                ),
                "red",
            )
            self.__app.set_status(SEROPENERROR.format(err), "red")
            self.__app.frm_banner.update_conn_status(DISCONNECTED)
            self.__app.frm_settings.enable_controls(DISCONNECTED)

    def connect_file(self):
        """
        Open binary data file connection.
        """

        in_filepath = self.__app.frm_settings.infilepath
        if in_filepath is None:
            return

        try:

            self._serial_object = open(in_filepath, "rb")
            self._serial_buffer = BufferedReader(self._serial_object)
            msg = f"{in_filepath}"
            self.connect_stream(self._serial_buffer, CONNECTED_FILE, msg)

        except (IOError, SerialException, SerialTimeoutException) as err:
            self._connected = False
            self.__app.set_connection(f"{in_filepath}", "red")
            self.__app.set_status(FILEOPENERROR.format(err), "red")
            self.__app.frm_banner.update_conn_status(DISCONNECTED)
            self.__app.frm_settings.enable_controls(DISCONNECTED)

    def connect_stream(self, stream, status, msg):
        """
        Connect to serial or file stream

        :param Stream stream: serial or file stream
        :param str status: serial or file
        :param str msg: connection descriptor message
        """

        self._reader = UBXReader(stream, quitonerror=QUITONERRORDEFAULT)

        if self.__app.frm_settings.datalogging:
            self.__app.file_handler.open_logfile()

        if self.__app.frm_settings.record_track:
            self.__app.file_handler.open_trackfile()

        self.__app.set_status("Connected", "blue")
        self.__app.frm_banner.update_conn_status(status)
        self.__app.frm_settings.enable_controls(status)
        self.__app.set_connection(msg, "green")
        self._connected = True
        if status == CONNECTED:  # serial
            self.start_read_thread()
        else:  # file
            self.start_readfile_thread()

    def disconnect(self):
        """
        Close serial connection.
        """

        if self._connected:
            try:
                self._reading = False
                self._reader = None
                self._serial_object.close()
                self.__app.frm_banner.update_conn_status(DISCONNECTED)
                self.__app.set_connection(NOTCONN, "red")
                self.__app.set_status("", "blue")

                if self.__app.frm_settings.datalogging:
                    self.__app.file_handler.close_logfile()

                if self.__app.frm_settings.record_track:
                    self.__app.file_handler.close_trackfile()

            except (SerialException, SerialTimeoutException):
                pass

        self._connected = False
        self.__app.frm_settings.enable_controls(self._connected)

    @property
    def port(self):
        """
        Getter for port
        """

        return self.__app.frm_settings.serial_settings().port

    @property
    def connected(self):
        """
        Getter for connection status
        """

        return self._connected

    @property
    def serial(self):
        """
        Getter for serial object
        """

        return self._serial_object

    @property
    def buffer(self):
        """
        Getter for serial buffer
        """

        return self._serial_buffer

    @property
    def thread(self):
        """
        Getter for serial thread
        """

        return self._serial_thread

    def serial_write(self, data: bytes):
        """
        Write binary data to serial port.

        :param bytes data: data to write to stream
        """

        try:
            self._serial_object.write(data)
        except (SerialException, SerialTimeoutException) as err:
            print(f"Error writing to serial port {err}")

    def start_read_thread(self):
        """
        Start the serial reader thread.
        """

        if self._connected:
            self._reading = True
            self.__app.frm_mapview.reset_map_refresh()
            self._serial_thread = Thread(target=self._read_thread(), daemon=True)
            self._serial_thread.start()

    def start_readfile_thread(self):
        """
        Start the file reader thread.
        """

        if self._connected:
            self._reading = True
            self.__app.frm_mapview.reset_map_refresh()
            self._file_thread = Thread(target=self._readfile_thread(), daemon=True)
            self._file_thread.start()

    def stop_read_thread(self):
        """
        Stop serial reader thread.
        """

        if self._serial_thread is not None:
            self._reading = False
            self._serial_thread = None

    def stop_readfile_thread(self):
        """
        Stop file reader thread.
        """

        if self._file_thread is not None:
            self._reading = False
            self._file_thread = None

    def _read_thread(self):
        """
        THREADED PROCESS
        Reads binary data from serial port and generates virtual event to
        trigger data parsing and widget updates.
        """

        try:
            while self._reading and self._serial_object:
                if self._serial_object.in_waiting:
                    self.__master.event_generate("<<ubx_read>>")
        except SerialException as err:
            self.__app.set_status(f"Error in read thread {err}", "red")
        # spurious errors as thread shuts down after serial disconnection
        except (TypeError, OSError):
            pass

    def _readfile_thread(self):
        """
        THREADED PROCESS
        Reads binary data from datalog file and generates virtual event to
        trigger data parsing and widget updates.
        """

        while self._reading and self._serial_object:
            self.__master.event_generate("<<ubx_readfile>>")

    def on_read(self, event):  # pylint: disable=unused-argument
        """
        Action on <<ubx_read>> event - read any data in the buffer.

        :param event event: read event
        """

        if self._reading and self._serial_object is not None:
            try:
                self._parse_data()
            except SerialException as err:
                self.__app.set_status(f"Error {err}", "red")

    def on_eof(self, event):  # pylint: disable=unused-argument
        """
        Action on end of file

        :param event event: eof event
        """

        self.disconnect()
        self.__app.set_status(ENDOFFILE, "blue")

    # def _parse_data(self, ser: Serial):
    def _parse_data(self):
        """
        Invoke the UBXReader.read() method to read and parse the data stream
        and direct to the appropriate UBX and/or NMEA protocol handler,
        depending on which protocols are filtered.
        """

        raw_data = None
        parsed_data = None
        protfilter = self.__app.frm_settings.protocol

        try:
            (raw_data, parsed_data) = self._reader.read()
            if raw_data is None:
                raise EOFError
        except EOFError:
            self.__master.event_generate("<<ubx_eof>>")
            return
        except (UBXParseError, NMEAParseError) as err:
            # log errors to console, then continue
            self.__app.frm_console.update_console(bytes(str(err), "utf-8"), err)
            return

        # print(f"DEBUG UBXReader._parse_data r:{raw_data} p:{parsed_data}")
        if raw_data is None or parsed_data is None:
            return
        msgprot = protocol(raw_data)
        if msgprot == ubt.UBX_PROTOCOL and msgprot & protfilter:
            self.__app.frm_console.update_console(raw_data, parsed_data)
            self.__app.ubx_handler.process_data(raw_data, parsed_data)
        elif msgprot == ubt.NMEA_PROTOCOL and msgprot & protfilter:
            self.__app.frm_console.update_console(raw_data, parsed_data)
            self.__app.nmea_handler.process_data(raw_data, parsed_data)
        elif msgprot == 0 and protfilter == 3:
            # log unknown protocol headers to console, then continue
            self.__app.frm_console.update_console(raw_data, parsed_data)

        # if datalogging, write to log file
        if self.__app.frm_settings.datalogging:
            self.__app.file_handler.write_logfile(raw_data, parsed_data)

    def flush(self):
        """
        Flush input buffer
        """

        if self._serial_buffer is not None:
            self._serial_buffer.flush()
        if self._serial_object is not None:
            self._serial_object.flushInput()
