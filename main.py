import argparse
import csv
import sys
from pprint import pformat
from trello import TrelloClient
from trello.exceptions import ResourceUnavailable

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
    "dateLastActivity",
    "due",
    "closed",
    "labels",
    "dateMovedToThisList",
]
LABEL_FIELDS = [
    'id',
    'name',
    'color',
]

def list_boards(client):
    all_boards = client.list_boards()
    for board in all_boards:
        print("{}: {}".format(board.id, board.name))

def get_cards_from_board(client, board_id, verbose, output_file, dump_extra_card_info_for):
    def verbose_print(*args, **kwargs):
        if verbose:
            print(*args, **kwargs)

    # initialise CSV rows
    csv_rows = []
    # initialise extra card info
    extra_card_info = []

    print("Reading cards from board...")

    # get the board
    try:
        board = client.get_board(board_id)
    except ResourceUnavailable:
        return "Error: could not find board with ID: {}".format(board_id)

    verbose_print("BOARD","\t"*1,board.name,":",board.id)
    
    # get its lists
    board_lists = board.list_lists()
    
    # step through lists in board
    for board_list in board_lists:
        verbose_print("LIST","\t"*2,board_list.name,":",board_list.id,"pos=",board_list.pos)
        # step through cards in list
        for card in board_list.list_cards():
            # start building CSV row
            csv_row = {}
            for field in BOARD_FIELDS:
                csv_row["board_{}".format(field)] = getattr(board, field)
            for field in BOARD_LIST_FIELDS:
                csv_row["board_list_{}".format(field)] = getattr(board_list, field)
            verbose_print("CARD","\t"*3,card.name)
            for field in CARD_FIELDS:
                val = getattr(card, field, None)
                # extra processing for labels
                if field == "labels":
                    if val:
                        val = [{lf: getattr(label, lf) for lf in LABEL_FIELDS} for label in val]
                    else:
                        val = []
                # extra processing for dateMovedToThisList
                if field == "dateMovedToThisList":
                    # get card movements
                    card_movements = card.list_movements()
                    if card_movements:
                        # remove movements to other lists
                        card_movements = [x for x in card_movements if x["destination"]["id"] == board_list.id]
                        # sort by datetime, newest first
                        card_movements.sort(key=lambda x: x["datetime"], reverse=True)
                        # grab newest
                        val = card_movements[0]["datetime"]
                    else:
                        # no movements found, pass through a None
                        # TODO: can we find date of card creation to go here instead?
                        val = None
                # add card fields to CSV row
                csv_row["card_{}".format(field)] = val
                verbose_print("CARD","\t"*4,"{}: {}".format(field, val))
            # add CSV row to CSV row list
            csv_rows.append(csv_row)
            # do we need to dump extra card info?
            if card.id == dump_extra_card_info_for:
                print("Dumping extra card info for {} ({})".format(card.id, card.name))
                extra_card_info.append("Name = " + card.name)
                extra_card_info.append("ID = " + card.id)
                extra_card_info.append("Movements = " + pformat(card.list_movements()))
                extra_card_info.append("Extra card info = " + pformat(card.__dict__))

    # build CSV field names
    field_names = []
    field_names.extend(["board_{}".format(x) for x in BOARD_FIELDS])
    field_names.extend(["board_list_{}".format(x) for x in BOARD_LIST_FIELDS])
    field_names.extend(["card_{}".format(x) for x in CARD_FIELDS])

    # write CSV rows
    print("Writing CSV output to {}...".format(output_file))
    with open(output_file, "w", newline="") as f:
        csvfile = csv.DictWriter(f, field_names)
        csvfile.writeheader()
        csvfile.writerows(csv_rows)

    # do we need to dump extra card info?
    if extra_card_info:
        with open("extra_card_info.txt", "w") as f:
            f.write("\n".join(extra_card_info))

    print("Done!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Query Trello API for card information")
    parser.add_argument('key', help='Your Trello API key')
    parser.add_argument('token', help='Your Trello service token')
    parser.add_argument('board_id', help='ID of board to query (if not supplied, will list all available boards and exit)', nargs="?")
    parser.add_argument('-o', '--output_file', help='File to receive results (default = "output.csv")', nargs="?", default="output.csv")
    parser.add_argument('--dump_extra_card_info_for', metavar='CARD_ID', help='If card with id matching "CARD_ID" is found dump all card fields to "extra_card_info.txt"', default=None)
    parser.add_argument('--omit_ids', help='Remove ID numbers from output', action="store_true")
    parser.add_argument('-v', '--verbose', help='Display extra information', action="store_true")
    args = parser.parse_args()

    # set up client
    client = TrelloClient(
        api_key=args.key,
        token=args.token,
    )

    if args.omit_ids:
        for field_list in BOARD_FIELDS, BOARD_LIST_FIELDS, CARD_FIELDS, LABEL_FIELDS:
            field_list.remove("id")
    board_id = args.board_id
    if not board_id:
        print("No board ID was supplied, listing all available boards...")
        print()
        list_boards(client)
    else:
        return_code = get_cards_from_board(client, board_id, args.verbose, args.output_file, args.dump_extra_card_info_for)
        # if anything other than None was returned from the function, it will be an error string
        # sys.exit will print it and exit with return code 1 (failure)
        # otherwise, if None was returned, it will print nothing and exit with code 0 (success)
        sys.exit(return_code)
