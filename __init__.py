#!/usr/bin/python

import os
import sqlite3
import time
from datetime import datetime
from shutil import copyfile
from sqlite3 import Error
import sys
import tty
import termios


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn


def get_all_memos(conn):
    """
    Query all rows in the tasks ZCLOUDRECORDING
    :param conn: the Connection object
    :return:
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM ZCLOUDRECORDING ORDER BY ZDATE")

    return cur.fetchall()


def main():
    cols = [{"n": "Date",
             "w": 19},
            {"n": "Duration",
             "w": 12},
            {"n": "Old Path",
             "w": 50},
            {"n": "New Path",
             "w": 70},
            {"n": "Status",
             "w": 20}]

    def getWidth(n):
        for c in cols:
            if c["n"] == n:
                return c["w"]
        return False

    def helper_str(c):
        return c.join(["{" + str(i) + ":" + str(c["w"]) + "}" for i, c in enumerate(cols)])

    def body_line(l):
        return "│ " + helper_str(" │ ").format(*l) + " │"

    database = "CloudRecordings.db"

    # create a database connection
    conn = create_connection(database)
    with conn:
        rows = get_all_memos(conn)

    datetime_offset = datetime(2019, 12, 5, 21, 20, 0).timestamp() - 597269999.174768

    if rows:
        export_folder = "export"
        try:
            os.stat(export_folder)
        except:
            os.mkdir(export_folder)

        print("=> Press enter to export this memo (or ESC to go to next memo)...")
        print()
        print("┌─" + helper_str("─┬─").format(*["─" * c["w"] for c in cols]) + "─┐")
        print("│ " + helper_str(" │ ").format(*[c["n"] for c in cols]) + " │")
        print("├─" + helper_str("─┼─").format(*["─" * c["w"] for c in cols]) + "─┤")

        for row in rows:
            date = datetime.fromtimestamp(row[5] + datetime_offset)
            date_str = date.strftime("%Y-%m-%d-%H-%M-%S")
            duration_str = time.strftime('%Hh %Mm %Ss', time.gmtime(row[6]))
            label = row[9].encode('ascii', 'ignore').decode("ascii").replace("/", "_")
            path_old = row[10] if row[10] else ""
            path_new = date_str + " " + label + path_old[path_old.rfind("."):] if path_old else ""
            path_new = os.path.join(export_folder, path_new) if path_new else ""
            if len(path_old) < getWidth("Old Path") - 3:
                path_old_short = path_old
            else:
                path_old_short = "..." + path_old[-getWidth("Old Path") + 3:]
            if len(path_new) < getWidth("New Path") - 3:
                path_new_short = path_new
            else:
                path_new_short = "..." + path_new[-getWidth("New Path") + 3:]

            if not path_old:
                print(body_line((date_str, duration_str, path_old_short, path_new_short, "No File")))
            else:
                print(body_line((date_str, duration_str, path_old_short, path_new_short, "Export?")), end="\r")
                key = 0
                fd = sys.stdin.fileno()
                old = termios.tcgetattr(fd)
                new = termios.tcgetattr(fd)
                new[3] = new[3] & ~termios.ECHO
                termios.tcsetattr(fd, termios.TCSADRAIN, new)
                tty.setcbreak(sys.stdin)
                while key not in (10, 27):
                    try:
                        key = ord(sys.stdin.read(1))
                        # print("Key: {}".format(key))
                    finally:
                        termios.tcsetattr(fd, termios.TCSADRAIN, old)
                if key == 10:
                    copyfile(path_old, path_new)
                    mod_time = time.mktime(date.timetuple())
                    os.utime(path_new, (mod_time, mod_time))
                    print(body_line((date_str, duration_str, path_old_short, path_new_short, "Exported!")))
                elif key == 27:
                    print(body_line((date_str, duration_str, path_old_short, path_new_short, "Not Exported")))

        print("└─" + helper_str("─┴─").format(*["─" * c["w"] for c in cols]) + "─┘")


if __name__ == '__main__':
    main()
