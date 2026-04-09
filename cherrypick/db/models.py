from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True)
    place_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False)
    address = Column(Text)
    category = Column(String(255))
    google_rating = Column(Float)
    total_review_count = Column(Integer)
    google_maps_url = Column(Text, nullable=False)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    reviews = relationship("Review", back_populates="business", cascade="all, delete-orphan")
    trust_reports = relationship("TrustReport", back_populates="business", cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    reviewer_name = Column(String(255))
    reviewer_profile_url = Column(Text)
    reviewer_total_reviews = Column(Integer)
    star_rating = Column(Integer, nullable=False)
    review_date = Column(String(100))
    review_text = Column(Text)
    photo_count = Column(Integer, default=0)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="reviews")
    analysis = relationship("ReviewAnalysis", back_populates="review", uselist=False, cascade="all, delete-orphan")


class ReviewAnalysis(Base):
    __tablename__ = "review_analyses"

    id = Column(Integer, primary_key=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False, unique=True, index=True)
    timing_score = Column(Float, default=0.0)
    rating_dist_score = Column(Float, default=0.0)
    single_review_score = Column(Float, default=0.0)
    text_similarity_score = Column(Float, default=0.0)
    text_quality_score = Column(Float, default=0.0)
    sentiment_mismatch_score = Column(Float, default=0.0)
    combined_score = Column(Float, default=0.0)
    claude_fake_probability = Column(Float, nullable=True)
    claude_reasoning = Column(Text, nullable=True)
    classification = Column(String(20))
    analyzed_at = Column(DateTime, default=datetime.utcnow)

    review = relationship("Review", back_populates="analysis")


class TrustReport(Base):
    __tablename__ = "trust_reports"

    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    trust_score = Column(Integer, nullable=False)
    adjusted_rating = Column(Float)
    red_flags = Column(JSON)
    summary_stats = Column(JSON)
    generated_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="trust_reports")
