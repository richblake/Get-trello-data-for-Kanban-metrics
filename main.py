import argparse
import csv
from trello import TrelloClient

BOARD_FIELDS = [
    "id",
    "name",
]
BOARD_LIST_FIELDS = [
    "id",
    "name",
    "pos",
]
CARD_FIELDS = [
    "id",
    "name",
    "pos",
]

ALL_FIELDS = []
ALL_FIELDS.extend(["board_{}".format(x) for x in BOARD_FIELDS])
ALL_FIELDS.extend(["board_list_{}".format(x) for x in BOARD_LIST_FIELDS])
ALL_FIELDS.extend(["card_{}".format(x) for x in CARD_FIELDS])

def quick_and_dirty_test(client):
    # initialise CSV rows
    csv_rows = []

    # # Working with all boards
    # all_boards = client.list_boards()
    # last_board = all_boards[-1]
    # print("BOARD","\t"*1,last_board.name,":",last_board.id)

    # get the dummy board
    test_board = client.get_board("5fa153fa57a674452896595e")
    print("BOARD","\t"*1,test_board.name,":",test_board.id)
    
    # get its lists
    board_lists = test_board.list_lists()
    
    # step through lists in board
    for board_list in board_lists:
        print("LIST","\t"*2,board_list.name,":",board_list.id,"pos=",board_list.pos)
        # step through cards in list
        for card in board_list.list_cards():
            # start building CSV row
            csv_row = {}
            for field in BOARD_FIELDS:
                csv_row["board_{}".format(field)] = getattr(test_board, field)
            for field in BOARD_LIST_FIELDS:
                csv_row["board_list_{}".format(field)] = getattr(board_list, field)
            print("CARD","\t"*3,card.name)
            for field in CARD_FIELDS:
                val = getattr(card,field)
                # add card fields to CSV row
                csv_row["card_{}".format(field)] = val
                print("CARD","\t"*4,"{}: {}".format(field, val))
            # add CSV row to CSV row list
            csv_rows.append(csv_row)

    # write CSV rows
    TEST_OUTPUT = "test.csv"
    with open(TEST_OUTPUT, "w", newline="") as f:
        csvfile = csv.DictWriter(f, ALL_FIELDS)
        csvfile.writeheader()
        csvfile.writerows(csv_rows)
    print("CSV output written to {}".format(TEST_OUTPUT))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('key', help='A Trello API key')
    parser.add_argument('token', help='A Trello service token')
    args = parser.parse_args()

    # set up client
    client = TrelloClient(
        api_key=args.key,
        token=args.token,
    )
    quick_and_dirty_test(client)
    