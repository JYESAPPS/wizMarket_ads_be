from app.db.connect import get_re_db_connection, close_cursor, close_connection  # 네가 쓰는 공통 유틸 가정
import pymysql

def insert_concierge_user_history(
    user_id: int,
    image_path: str,
    caption: str,
    channel: int,
    register_tag: str | None,
) -> int:
    """
    concierge_user_history 에 PENDING 상태로 1행 INSERT 하고
    생성된 history_id 반환
    """
    connection = get_re_db_connection()
    cursor = None

    try:
        cursor = connection.cursor()
        sql = """
            INSERT INTO concierge_user_history
                (user_id, image_path, caption, channel, register_tag, insta_status)
            VALUES
                (%s, %s, %s, %s, %s, 'PENDING')
        """
        cursor.execute(
            sql,
            (
                user_id,
                image_path,
                caption,
                channel,
                register_tag,
            ),
        )
        connection.commit()
        return cursor.lastrowid
    except pymysql.MySQLError as e:
        connection.rollback()
        print(f"[insert_concierge_user_history] DB error: {e}")
        raise
    finally:
        close_cursor(cursor)
        close_connection(connection)


def update_concierge_user_history_status(
    history_id: int,
    status: str,
    insta_media_id: str | None = None,
    error_message: str | None = None,
) -> None:
    """
    concierge_user_history 의 insta_status / insta_media_id / error_message 업데이트
    status: 'PENDING' | 'SUCCESS' | 'FAILED'
    """
    connection = get_re_db_connection()
    cursor = None

    try:
        cursor = connection.cursor()
        sql = """
            UPDATE concierge_user_history
               SET insta_status  = %s,
                   insta_media_id = %s,
                   error_message  = %s,
                   updated_at     = NOW()
             WHERE history_id    = %s
        """
        cursor.execute(
            sql,
            (
                status,
                insta_media_id,
                error_message,
                history_id,
            ),
        )
        connection.commit()
    except pymysql.MySQLError as e:
        connection.rollback()
        print(f"[update_concierge_user_history_status] DB error: {e}")
        raise
    finally:
        close_cursor(cursor)
        close_connection(connection)
