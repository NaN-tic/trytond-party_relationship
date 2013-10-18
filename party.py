from sql import Union, As

from trytond.pool import Pool, PoolMeta
from trytond.model import ModelSQL, ModelView, fields

__all__ = ['RelationType', 'PartyRelation', 'PartyRelationAll', 'Party']
__metaclass__ = PoolMeta


class RelationType(ModelSQL, ModelView):
    'Relation Type'
    __name__ = 'party.relation.type'

    name = fields.Char('Name', required=True, translate=True)
    reverse = fields.Many2One('party.relation.type', 'Reverse Relation',
        ondelete='CASCADE')

    @classmethod
    def __setup__(cls):
        super(RelationType, cls).__setup__()
        cls._error_messages.update({
                'same_relation': 'You can not select the same relation as '
                    'reverse relation.',
            })

    @classmethod
    def validate(cls, records):
        super(RelationType, cls).validate(records)
        for record in records:
            record.check_reverse()

    def check_reverse(self):
        if self.reverse and self.reverse.id == self.id:
            self.raise_user_error('same_relation')


class PartyRelation(ModelSQL):
    'Party Relation'
    __name__ = 'party.relation'

    from_ = fields.Many2One('party.party', 'From', required=True, select=True,
        ondelete='CASCADE')
    to = fields.Many2One('party.party', 'To', required=True, select=True,
        ondelete='CASCADE')
    type = fields.Many2One('party.relation.type', 'Type', required=True,
        select=True, ondelete='CASCADE')


class PartyRelationAll(PartyRelation, ModelView):
    'Party Relation'
    __name__ = 'party.relation.all'

    @staticmethod
    def table_query():
        pool = Pool()
        Relation = pool.get('party.relation')
        Type = pool.get('party.relation.type')

        relation = Relation.__table__()
        type = Type.__table__()

        main_columns = (relation.create_uid, relation.create_date,
            relation.write_uid, relation.write_date)
        cols = main_columns + (As(relation.id * 2, 'id'),
            relation.from_, relation.to, relation.type)
        query = relation.select(*cols)

        cols = main_columns + (As(relation.id * 2 + 1, 'id'),
            relation.to.as_('from_'), relation.from_.as_('to'), type.reverse)
        reverse_query = relation.join(type, condition=relation.type == type.id)
        reverse_query = reverse_query.select(*cols)
        query = Union(query, reverse_query, all_=True)

        return query

    @staticmethod
    def convert_instances(relations):
        " Converts party.relation.all instances to party.relation "
        pool = Pool()
        Relation = pool.get('party.relation')
        return Relation.browse(list(set([int(x.id / 2) for x in relations])))

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        Relation = pool.get('party.relation')
        return Relation.create(vlist)

    @classmethod
    def write(cls, relations, values):
        pool = Pool()
        Relation = pool.get('party.relation')
        return Relation.write(cls.convert_instances(relations), values)

    @classmethod
    def delete(cls, relations):
        pool = Pool()
        Relation = pool.get('party.relation')
        return Relation.delete(cls.convert_instances(relations))


class Party:
    __name__ = 'party.party'

    relations = fields.One2Many('party.relation.all', 'from_', 'Relations')
