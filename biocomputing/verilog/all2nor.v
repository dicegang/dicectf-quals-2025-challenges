(* techmap_celltype = "BUF" *)
module NOR_BUF (input A, output Y);
	wire out1;
	NOR1 u1 (.A(A), .Y(out1));
	NOR1 u2 (.A(A), .Y(Y));
endmodule

(* techmap_celltype = "NAND" *)
module NOR_NAND (input A, input B, output Y);
	wire not_A;
    wire not_B;
    wire nor_out;

	NOR1 u1 (.A(A), .Y(not_A));
	NOR1 u2 (.A(B), .Y(not_B));
    NOR2 u3 (.A(not_A), .B(not_B), .Y(nor_out));
    NOR1 u4 (.A(nor_out), .Y(Y));
endmodule

(* techmap_celltype = "DFF_PP0" *)
module DFF_PP0(input C, input D, input R, output Q);
    wire not_R;
    wire C_nand_R;
    wire D_nand_Feedback;
    wire C_nand_not_R;
    wire nand_1;
    wire nand_2;
    wire nand_3;
    wire nand_dff_1;
    wire nand_dff_2;
    wire nand_QBAR;

    NOR1 u0 (.A(R), .Y(not_R));
    NAND u1 (.A(not_R), .B(C), .Y(C_nand_not_R));
    NAND u2 (.A(D), .B(nand_dff_1), .Y(D_nand_Feedback));
    NAND u3 (.A(D_nand_Feedback), .B(nand_dff_2), .Y(nand_1));
    NAND u4 (.A(nand_1), .B(not_R), .Y(nand_2));
    NAND u5 (.A(nand_2), .B(nand_2), .Y(nand_3));
    NAND u6 (.A(nand_2), .B(C_nand_not_R), .Y(nand_dff_1));
    NAND u7 (.A(nand_3), .B(C_nand_not_R), .Y(nand_dff_2));
    NAND u8 (.A(nand_dff_1), .B(Q), .Y(nand_QBAR));
    NAND u9 (.A(nand_dff_2), .B(nand_QBAR), .Y(Q));
endmodule