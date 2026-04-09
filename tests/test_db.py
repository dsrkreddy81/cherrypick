from cherrypick.db.session import get_engine, create_tables
from cherrypick.db.models import Business, Review, ReviewAnalysis, TrustReport
from sqlalchemy import inspect


def test_create_tables_creates_all_four_tables():
    engine = get_engine()
    create_tables(engine)
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    assert "businesses" in table_names
    assert "reviews" in table_names
    assert "review_analyses" in table_names
    assert "trust_reports" in table_names
