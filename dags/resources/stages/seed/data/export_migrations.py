import decimal
import json


def export_migrations():
    # The file can be downloaded from https://api.tzkt.io/v1/operations/migrations?limit=10000
    migrations = json.loads(open('tzkt_migrations.json').read(), parse_float=decimal.Decimal)

    output_file = open('migrations.json', 'w')
    for migration in migrations:
        output_file.write(json.dumps({
            'level': migration.get('level'),
            'timestamp': migration.get('timestamp'),
            'block_hash': migration.get('block'),
            'kind': migration.get('kind'),
            'address': migration.get('account', {}).get('address'),
            'balance_change': migration.get('balanceChange'),
        }) + '\n')
        print(migration)


export_migrations()
