import os
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from fastapi import FastAPI, Depends, HTTPException, Query

# ------------------
# DBセットアップ
# ------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://app:pass@db:5432/appdb",  # デフォルト値（環境変数なくても動くように）
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------
# モデル定義（SQLAlchemy）
# ------------------

class PlotModel(Base):
    __tablename__ = "plots"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    work = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)
    summary = Column(Text, nullable=True)


# ------------------
# Pydanticスキーマ
# ------------------

class PlotBase(BaseModel):
    title: str
    work: str
    status: str
    summary: Optional[str] = None


class PlotCreate(PlotBase):
    pass


class PlotRead(PlotBase):
    id: int

    class Config:
        orm_mode = True


# ------------------
# FastAPI本体
# ------------------

app = FastAPI()


@app.on_event("startup")
def on_startup():
    # コンテナ起動時にテーブルがなければ作る
    Base.metadata.create_all(bind=engine)


@app.get("/ping")
def ping():
    return {"message": "pong"}


@app.get("/plots", response_model=List[PlotRead])
def list_plots(
    work: Optional[str] = Query(None, description="作品名でフィルタ"),
    status: Optional[str] = Query(None, description="ステータスでフィルタ"),
    q: Optional[str] = Query(None, description="タイトル・概要のキーワード検索"),
    db: Session = Depends(get_db),
):
    """プロット一覧を返す（フィルタ・検索対応）"""

    query = db.query(PlotModel)

    if work:
        query = query.filter(PlotModel.work == work)

    if status:
        query = query.filter(PlotModel.status == status)

    if q:
        like = f"%{q}%"
        query = query.filter(
            PlotModel.title.ilike(like) | PlotModel.summary.ilike(like)
        )

    plots = query.order_by(PlotModel.id.asc()).all()
    return plots


@app.get("/plots/{plot_id}", response_model=PlotRead)
def get_plot(plot_id: int, db: Session = Depends(get_db)):
    """指定IDのプロット1件を返す"""
    plot = db.query(PlotModel).filter(PlotModel.id == plot_id).first()
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
    return plot



@app.post("/plots", response_model=PlotRead)
def create_plot(data: PlotCreate, db: Session = Depends(get_db)):
    """プロットを1件追加する"""
    plot = PlotModel(
        title=data.title,
        work=data.work,
        status=data.status,
        summary=data.summary,
    )
    db.add(plot)
    db.commit()
    db.refresh(plot)
    return plotF


@app.put("/plots/{plot_id}", response_model=PlotRead)
def update_plot(plot_id: int, data: PlotCreate, db: Session = Depends(get_db)):
    plot = db.query(PlotModel).filter(PlotModel.id == plot_id).first()
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")

    plot.title = data.title
    plot.work = data.work
    plot.status = data.status
    plot.summary = data.summary

    db.commit()
    db.refresh(plot)
    return plot

@app.delete("/plots/{plot_id}")
def delete_plot(plot_id: int, db: Session = Depends(get_db)):
    plot = db.query(PlotModel).filter(PlotModel.id == plot_id).first()
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")

    db.delete(plot)
    db.commit()
    return {"message": "deleted", "id": plot_id}

