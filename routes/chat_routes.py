from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from database import db, Order, Message

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/orders/<int:order_id>/chat', methods=['GET'])
@login_required
def order_chat(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Access Control: Only the buyer or the seller of this order can view the specifications chat
    if order.buyer_id != current_user.id and order.seller_id != current_user.id:
        flash("You do not have authorization to view this chat room.", "danger")
        return redirect(url_for('profile.view_profile'))
        
    messages = Message.query.filter_by(order_id=order_id).order_by(Message.created_at.asc()).all()
    
    # Determine who the recipient is relative to current_user
    recipient = order.seller_user if current_user.id == order.buyer_id else order.buyer
    
    return render_template(
        'orders/chat.html',
        order=order,
        messages=messages,
        recipient=recipient
    )

@chat_bp.route('/orders/<int:order_id>/chat/send', methods=['POST'])
@login_required
def send_message(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Access Control: Only the buyer or the seller of this order can send messages
    if order.buyer_id != current_user.id and order.seller_id != current_user.id:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('profile.view_profile'))
        
    text = request.form.get('message_text', '').strip()
    if not text:
        flash("Message body cannot be blank.", "warning")
        return redirect(url_for('chat.order_chat', order_id=order_id))
        
    # Save the new message
    new_message = Message(
        order_id=order_id,
        sender_id=current_user.id,
        text=text
    )
    
    db.session.add(new_message)
    db.session.commit()
    
    return redirect(url_for('chat.order_chat', order_id=order_id))
