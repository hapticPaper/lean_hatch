-- PostgreSQL function and triggers for real-time notifications
-- Run this SQL in your PostgreSQL database

-- Create notification function
CREATE OR REPLACE FUNCTION notify_message_changes()
RETURNS TRIGGER AS $$
BEGIN
    -- Send notification with conversation_id and action type
    PERFORM pg_notify('message_changes', json_build_object(
        'conversation_id', COALESCE(NEW.conversation_id, OLD.conversation_id),
        'action', TG_OP,
        'message_id', COALESCE(NEW.id, OLD.id)
    )::text);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Create triggers for INSERT, UPDATE, DELETE on messages table
DROP TRIGGER IF EXISTS messages_notify_trigger ON messages;
CREATE TRIGGER messages_notify_trigger
    AFTER INSERT OR UPDATE OR DELETE ON messages
    FOR EACH ROW
    EXECUTE FUNCTION notify_message_changes();
