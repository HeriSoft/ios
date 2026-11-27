import { useLocalSearchParams } from "expo-router";
import React from "react";
import { ProductDetail } from "../src/components/ProductDetail";
import { EmptyState } from "../src/components/ui";
import { foodById, foodProduct } from "../src/core/foods";
import { useStore } from "../src/state/store";

/** Chi tiết sản phẩm/món ăn. `?food=<id>` mở thẳng một món trong bảng (dùng cho liên kết và kiểm thử). */
export default function ProductScreen() {
  const { food } = useLocalSearchParams<{ food?: string }>();
  const store = useStore();
  const fromParam = food ? foodById(food) : undefined;
  const product = fromParam ? foodProduct(fromParam) : store.product;
  if (!product) return <EmptyState title="Chưa chọn sản phẩm" />;
  return <ProductDetail product={product} preferServings={fromParam ? true : store.preferServings} />;
}
