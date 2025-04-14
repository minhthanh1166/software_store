<?php 

    /*
    File order.php
    Đây là file chính. Dùng để tạo đơn hàng và hiển thị giao diện cổng thanh toán (Checkout)
    
    URL tạo đơn hàng:           https://yourwebsite.tld/order.php
    URL giao diện thanh toán:   https://yourwebsite.tld/order.php?id={order_id}
    
    */
    // Include file db_connect.php, file chứa toàn bộ kết nối CSDL
    require('db_connect.php');
   
   // Khởi tạo biến $order_id
    if(isset($_GET["id"]) && is_numeric($_GET["id"]))
        $order_id = $_GET["id"];
    else 
        $order_id = '';
        
    // Nếu method là POST thì tạo đơn hàng
    if (isset($_POST) && isset($_POST["total"])) {
        
        $order_total = $_POST["total"];
        if(is_numeric($order_total)) {
           
            // Cố định tên cho đơn hàng
            $name = "Kem Merino";
            
            // Tao query SQL insert dữ liệu đơn hàng vào bảng tb_orders
            $sql = "INSERT INTO tb_orders (total, name) VALUES ('{$order_total}', '{$name}')";
             
            // Nếu query insert thành công
            if ($conn->query($sql) === TRUE) {
                
                // Lấy ID của đơn hàng vừa insert
                $order_id = $conn->insert_id;
                
                // Redirect đến trang checkout để hiển thị giao diện thanh toán
                header("Location: https://payment-gateway-demo.sepay.dev/order.php?id=" . $order_id);
    
            } else {
                echo json_encode(['success'=>FALSE, 'message' => 'Can not insert record to mysql: ' . $conn->error]);
            }
        }
    } 
   
?>
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>SePay Demo</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
  </head>
  <body>
    <div class="row my-5 px-2">
        <div class="col-md-8 mx-auto">
            
            <!-- Form tạo đơn hàng. Mặc định hiển thị form này khi vào https://123host.asia/sepay/order.php -->
            <?php if(!is_numeric($order_id)) { ?>
            <h1>Đặt hàng</h1>
            <form  method="POST" action="">
                  
              <div class="mb-3">
                <label for="amountInput" class="form-label">Số tiền</label>
                <input type="number" name="total" class="form-control" id="amountInput" aria-describedby="emailHelp" value="3000">
                <div id="amountInputHelp" class="form-text">Điền số tiền</div>
              </div>
               
              <button type="submit" class="btn btn-primary">Đặt hàng</button>
            </form>
            
            <?php } else { ?>
            <!-- Form tạo đơn hàng -->
            
            <!-- Hiển thị Giao diện thanh toán (Checkout) khi tạo đơn hàng thành công-->
            <?php 
                // Lấy thông tin đơn hàng
                 $result = $conn->query("SELECT * FROM tb_orders where id={$order_id}");
                if ($result) {
                  $order_details = $result->fetch_object();
                    if(!$order_details)
                    die('Không tìm thấy đơn hàng');

                } else {
                    die('Không tìm thấy đơn hàng');

                } 
            ?>
            
           
<div class="row">
    <div class="col-md-8">
         <h1><svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="currentColor" class="bi bi-check-circle text-success" viewBox="0 0 16 16">
  <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14m0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16"/>
  <path d="m10.97 4.97-.02.022-3.473 4.425-2.093-2.094a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05"/>
</svg> Đặt hàng thành công</h1>
<span class="text-muted">Mã đơn hàng #DH<?= $order_id;?></span>
<div id="success_pay_box" class="p-2 text-center pt-3 border border-2 mt-5" style="display:none">
    <h2 class="text-success"><svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="currentColor" class="bi bi-check-circle text-success" viewBox="0 0 16 16">
  <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14m0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16"/>
  <path d="m10.97 4.97-.02.022-3.473 4.425-2.093-2.094a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05"/>
</svg> Thanh toán thành công</h2>
<p class="text-center text-success">Chúng tôi đã nhận được thanh toán, đơn hàng sẽ được chuyển đến quý khách trong thời gian sớm nhất!</p>
</div>
<div class="row mt-5 px-2" id="checkout_box">
    <div class="col-12 text-center my-2 border"><p class="mt-2">Hướng dẫn thanh toán qua chuyển khoản ngân hàng</p></div>
    <div class="col-md-6 border text-center p-2">
        <p class="fw-bold">Cách 1: Mở app ngân hàng và quét mã QR</p>
        <div class="my-2">
            <img src="https://qr.sepay.vn/img?bank=MBBank&acc=0903252427&template=compact&amount=<?= intval($order_details->total);?>&des=DH<?= $order_id;?>" class="img-fluid">
            <span>Trạng thái: Chờ thanh toán... <div class="spinner-border" role="status">
  <span class="sr-only"></span>
</div></span>
        </div>
    </div>
    <div class="col-md-6 border p-2">
        <p class="fw-bold">Cách 2: Chuyển khoản thủ công theo thông tin</p>
        <div class="text-center"><img src="https://qr.sepay.vn/assets/img/banklogo/MB.png" class="img-fluid" style="max-height:50px">
        <p class="fw-bold">Ngân hàng MBBank</p></div>
        
        <table class="table">
            <tbody>
                <tr>
                    <td>Chủ tài khoản: </td>
                    <td><b>Bùi Tấn Việt</b></td>
                </tr>
                 <tr>
                    <td>Số TK: </td>
                    <td><b>0903252427</b></td>
                </tr>
                 <tr>
                    <td>Số tiền: </td>
                    <td><b><?= number_format($order_details->total);?>đ</b></td>
                </tr>
                 <tr>
                    <td>Nội dung CK: </td>
                    <td><b>DH<?= $order_details->id;?></b></td>
                </tr>
            </tbody>
        </table>
        <p class="bg-light p-2">Lưu ý: Vui lòng giữ nguyên nội dung chuyển khoản DH<?= $order_details->id;?> để hệ thống tự động xác nhận thanh toán</p>
    </div>
</div>
    </div>
    <div class="col-md-4 bg-light border-top">
        <p class="fw-bold">Thông tin đơn hàng</p>
        <table class="table">
            <tbody>
                <tr>
                    <td><span class="fw-bold"><?= $order_details->name;?></span></td>
                    <td class="text-end fw-bold"><?= number_format($order_details->total);?>đ</td>
                </tr>
                <tr>
                    <td>Thuế</td>
                    <td class="text-end">-</td>
                </tr>
                 <td><span class="fw-bold">Tổng</span></td>
                <td class="text-end fw-bold"><?= number_format($order_details->total);?>đ</td>
            </tr>
            </tbody>
        </table>
        
    </div>
</div>
<div>
    <p class="mt-5"><a class="text-decoration-none" href="https://payment-gateway-demo.sepay.dev/order.php"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-chevron-left" viewBox="0 0 16 16">
  <path fill-rule="evenodd" d="M11.354 1.646a.5.5 0 0 1 0 .708L5.707 8l5.647 5.646a.5.5 0 0 1-.708.708l-6-6a.5.5 0 0 1 0-.708l6-6a.5.5 0 0 1 .708 0"/>
</svg> Quay lại</a></p>
</div>


            <!-- Hiển thị Giao diện thanh toán (Checkout) khi tạo đơn hàng thành công-->

            <?php } ?>

            

        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz" crossorigin="anonymous"></script>
      <script src="https://code.jquery.com/jquery-1.10.2.js"></script>
      
      
      <?php
        // Nếu đang ở giao diện checkout
      if(isset($order_id)) {?>
      <script>
      var pay_status = 'Unpaid';
      
      // Hàm kiểm tra trạng thái đơn hàng
      // Sử dụng Ajax để lấy trạng thái đơn hàng. Nếu thanh toán thành công thì hiển thị Box đã thanh toán thành công, ẩn box checkout
      function check_payment_status() {
          if(pay_status == 'Unpaid') {
               $.ajax({
                    type: "POST",
                    data: {order_id: <?= $order_id;?>},
                    url: "check_payment_status.php",
                    dataType:"json",
                    success: function(data){
                        if(data.payment_status == "Paid") {
                            $("#checkout_box").hide();
                            $("#success_pay_box").show();
                            pay_status = 'Paid';
                        }
                    }
                  });
              }
          }
        //Kiểm tra trạng thái đơn hàng 1 giây một lần
        setInterval(check_payment_status, 1000);
      </script>
      <?php } ?>

  </body>
</html>