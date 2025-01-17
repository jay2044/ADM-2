import sys
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsRectItem
)
from PyQt6.QtGui import QBrush, QPen, QColor
from PyQt6.QtCore import Qt, QRectF, QPointF

class DraggableRectItem(QGraphicsRectItem):
    def __init__(self, rect, parent=None):
        super().__init__(rect, parent)
        self.setFlags(
            QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable
        )
        self._mousePressOffset = QPointF()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Store the offset so the item doesn’t jump when dragged
            self._mousePressOffset = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            # Calculate new position
            new_pos = self.mapToScene(event.pos() - self._mousePressOffset)
            x = self.x()  # Keep X fixed; only move vertically
            y = new_pos.y()

            # Clamp the block to stay within the timeline (10..102 here)
            if y < 10:
                y = 10
            elif y > 102:  # 110 - block_height (8) = 102
                y = 102

            self.setPos(x, y)
        super().mouseMoveEvent(event)

def main():
    app = QApplication(sys.argv)

    # Scene and view setup
    scene = QGraphicsScene()
    scene.setSceneRect(0, 0, 200, 120)  # Wide enough, short in height

    # Draw the vertical timeline (24h) – here it's only 100px tall for compactness
    timeline_rect = QGraphicsRectItem(50, 10, 20, 100)
    timeline_rect.setPen(QPen(Qt.GlobalColor.black))
    timeline_rect.setBrush(QBrush(QColor("lightgray")))
    scene.addItem(timeline_rect)

    # Create the 2-hour block (8px tall if 24h => 100px total)
    block_height = 8
    block_width = 20
    block_item = DraggableRectItem(QRectF(50, 10, block_width, block_height))
    block_item.setBrush(QBrush(QColor("blue")))
    scene.addItem(block_item)

    # Show everything
    view = QGraphicsView(scene)
    view.setFixedSize(220, 140)  # Just enough to see the timeline
    view.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
