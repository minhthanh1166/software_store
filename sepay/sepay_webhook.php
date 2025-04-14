<?php

    /* 
    File sepay_webhook.php
    File này dùng làm endpoint nhận webhook từ SePay. Mỗi khi có giao dịch SePay sẽ bắn webhook về và chúng ta sẽ lưu thông tin giao dịch vào CSDL. Đồng thời bóc tách ID đơn hàng từ nội dung thanh toán. Sau khi tìm được ID đơn hàng thì cập nhật trạng thái thanh toán của đơn hàng thành đã thanh toán (payment_status=Paid).
     Xem hướng dẫn tạo tích hợp Webhook phía SePay tại https://docs.sepay.vn/tich-hop-webhooks.html
     Endpoint nhận webhook sẽ là https://yourwebsite.tld/sepay_webhook.php
    */
    
     // Include file db_connect.php, file chứa toàn bộ kết nối CSDL
    require('db_connect.php');
   
    // Lay du lieu tu webhooks, xem cac truong du lieu tai https://docs.sepay.vn/tich-hop-webhooks.html#du-lieu
    $data = json_decode(file_get_contents('php://input'));
    if(!is_object($data)) {
        echo json_encode(['success'=>FALSE, 'message' => 'No data']);
        die('No data found!');
    }
    
    // Khoi tao cac bien
    $gateway = $data->gateway;
    $transaction_date = $data->transactionDate;
    $account_number = $data->accountNumber;
    $sub_account = $data->subAccount;

    $transfer_type = $data->transferType;
    $transfer_amount = $data->transferAmount;
    $accumulated = $data->accumulated;

    $code = $data->code;
    $transaction_content = $data->content;
    $reference_number = $data->referenceCode;
    $body = $data->description;

    $amount_in = 0;
    $amount_out = 0;

    // Kiem tra giao dich tien vao hay tien ra
    if($transfer_type == "in")
        $amount_in = $transfer_amount;
    else if($transfer_type == "out")
        $amount_out = $transfer_amount;

    // Tao query SQL
    $sql = "INSERT INTO tb_transactions (gateway, transaction_date, account_number, sub_account, amount_in, amount_out, accumulated, code, transaction_content, reference_number, body) VALUES ('{$gateway}', '{$transaction_date}', '{$account_number}', '{$sub_account}', '{$amount_in}', '{$amount_out}', '{$accumulated}', '{$code}', '{$transaction_content}', '{$reference_number}', '{$body}')";

    // Chay query de luu giao dich vao CSDL
    if ($conn->query($sql) === TRUE) {
       // echo json_encode(['success'=>TRUE]);
    } else {
        echo json_encode(['success'=>FALSE, 'message' => 'Can not insert record to mysql: ' . $conn->error]);
    }
    
    // Tách mã đơn hàng
    
    // Biểu thức regex để khớp với mã đơn hàng
    $regex = '/DH(\d+)/';
    
    // Sử dụng preg_match để khớp regex với chuỗi nội dung chuyển tiền
    preg_match($regex, $transaction_content, $matches);
    
    // Lấy mã đơn hàng từ kết quả khớp
    $pay_order_id = $matches[1];

    // Nếu không tìm thấy mã đơn hàng từ nội dung thanh toán thì trả về kết quả lỗi
    if(!is_numeric($pay_order_id)) {
        echo json_encode(['success' => false, 'message' => 'Order not found. Order_id ' . $pay_order_id]);
        die();
    }
    
    // Tìm đơn hàng với mã đơn hàng và số tiền tương ứng với giao dịch thanh toán trên. Điều kiện là id đơn hàng, số tiền, trạng thái đơn hàng phải là 'Unpaid'
    $result = $conn->query("SELECT * FROM tb_orders where id={$pay_order_id} AND total={$amount_in} AND payment_status='Unpaid'");
    
    // Nếu không tìm thấy đơn hàng
    if(!$result) {
        echo json_encode(['success' => false, 'message' => 'Order not found. Order_id ' . $pay_order_id]);
        die();
    } else {
        // Tìm thấy đơn hàng, update trạng thái 
        $conn->query("UPDATE tb_orders SET payment_status='Paid' WHERE id='{$pay_order_id}'");
        echo json_encode(['success'=>TRUE]);

    }
    
    
    

?>