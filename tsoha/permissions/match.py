value = VisitorAttribute('value')

class Matcher(Visitor):
    def __init__(self, model):
        self.model = model

    @Visitor.visits(FilterExpression)
    @Visitor.consumes(Visitor.original, value)
    def visit_filter(self, expr, value):
        field_value = getattr(value, expr.name)

        return self.visit(
            expr.value,
            attrs={ value: field_value },
        )
    
    @Visitor.visits(JoinExpression)
    @Visitor.consumes(Visitor.original, value)
    def visit_join(self, expr, value):
        return self.visit(
        )