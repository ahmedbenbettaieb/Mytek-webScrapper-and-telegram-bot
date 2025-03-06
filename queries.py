# SQL queries
CREATE_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS pcs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    price DECIMAL(10, 2),
    ref VARCHAR(255),
    name VARCHAR(255),
    description TEXT,
    availability VARCHAR(50)
);
"""

INSERT_QUERY = """
INSERT INTO pcs (price, ref, name, description, availability)
VALUES (%s, %s, %s, %s, %s)
"""

GET_PCS_BY_NAME_QUERY = """
SELECT * FROM pcs
WHERE name LIKE %s
LIMIT 1
"""

# Query to get PCs by price range
GET_PCS_BY_PRICE_RANGE_QUERY = """
SELECT * FROM pcs
WHERE price BETWEEN %s AND %s
"""

# Query to get PCs by name and price range
GET_PCS_BY_NAME_AND_PRICE_RANGE_QUERY = """
SELECT * FROM pcs
WHERE name LIKE %s AND price BETWEEN %s AND %s
"""
